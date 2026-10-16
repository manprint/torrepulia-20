import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';

const base = '/website_torrepulia_theme/static/src/cinematic/campaign/';
const icons = '/website_torrepulia_theme/static/src/cinematic/icons/';

export class CampaignImages extends Interaction {
    static selector = '.tp-cinematic img[src*="/static/src/cinematic/campaign/"]';
    start() {
        const src = this.el.getAttribute('src');
        const match = src.match(/\/(hero|family|olive|land|still-life|bottle)-\d+\.webp$/);
        if (!match) return;
        const name = match[1];
        const widths = ['hero', 'land', 'still-life'].includes(name) ? [640, 1280, 1920] : [640, 1280, 1600];
        const original = ['srcset', 'sizes'].map(key => [key, this.el.getAttribute(key)]);
        this.el.srcset = widths.map(width => `${base}${name}-${width}.webp ${width}w`).join(', ');
        this.el.sizes = ['hero', 'still-life'].includes(name) ? '100vw' : '(max-width: 760px) 100vw, 50vw';
        this.registerCleanup(() => original.forEach(([key, value]) => value === null ? this.el.removeAttribute(key) : this.el.setAttribute(key, value)));
    }
}
registry.category('public.interactions').add('torrepulia.campaign.images', CampaignImages);

export class PhotoFilm extends Interaction {
    static selector = '.tp-cinematic .mc-section:has(video[data-photo-film])';
    start() {
        const video = this.el.querySelector('video[data-photo-film]');
        const button = this.el.querySelector('.mc-film-toggle');
        const photo = this.el.querySelector(':scope > img');
        const kind = video.dataset.photoFilm;
        if (!button || !photo?.getAttribute('src')?.startsWith(base + kind + '-')) return;
        const reduced = matchMedia('(prefers-reduced-motion: reduce)');
        const phone = matchMedia('(max-width: 760px)');
        const connection = navigator.connection;
        let visible = false;
        let stopped = false;
        let sourceKey;
        let disposed = false;
        video.muted = true;
        const syncButton = () => {
            const playing = !video.paused;
            const label = playing ? 'Metti in pausa animazione fotografica' : 'Riproduci animazione fotografica';
            button.setAttribute('aria-label', label);
            button.title = label;
            button.querySelector('img').src = icons + (playing ? 'pause.svg' : 'play.svg');
            button.hidden = reduced.matches;
        };
        const update = async () => {
            if (disposed) return;
            if (reduced.matches || connection?.saveData || stopped || !visible || document.hidden) {
                video.pause(); syncButton(); return;
            }
            const variant = phone.matches ? 'mobile' : 'desktop';
            if (sourceKey !== variant) {
                sourceKey = variant;
                video.classList.remove('is-playing');
                video.poster = base + `${kind}-${variant}-poster.webp`;
                const webm = !!video.canPlayType('video/webm; codecs="vp9"');
                video.src = base + `${kind}-${variant}.${webm ? 'webm' : 'mp4'}`;
                video.load();
            }
            try { await video.play(); } catch { /* The original photo remains visible if autoplay is refused. */ }
            if (!disposed) syncButton();
        };
        const observer = new IntersectionObserver(entries => {
            visible = entries[0].isIntersecting;
            update();
        }, { threshold: .15 });
        observer.observe(video);
        this.addListener(video, 'playing', () => { video.classList.add('is-playing'); syncButton(); });
        this.addListener(video, 'error', () => { video.classList.remove('is-playing'); syncButton(); });
        this.addListener(button, 'click', () => { stopped = !video.paused; update(); });
        this.addListener(reduced, 'change', () => {
            if (reduced.matches) video.classList.remove('is-playing');
            update();
        });
        this.addListener(phone, 'change', update);
        this.addListener(document, 'visibilitychange', update);
        button.classList.add('is-ready'); syncButton();
        this.registerCleanup(() => {
            disposed = true; observer.disconnect(); video.pause();
            video.removeAttribute('src'); video.load(); video.classList.remove('is-playing');
            video.poster = base + `${kind}-desktop-poster.webp`;
            button.classList.remove('is-ready'); button.hidden = false;
            button.setAttribute('aria-label', 'Riproduci animazione fotografica');
            button.title = 'Riproduci animazione fotografica';
            button.querySelector('img').src = icons + 'play.svg';
        });
    }
}
registry.category('public.interactions').add('torrepulia.campaign.film', PhotoFilm);

export class CampaignDesign extends Interaction {
    static selector = '.tp-cinematic .mc-section:has(.bottle-portrait, .process)';
    start() {
        const reduced = matchMedia('(prefers-reduced-motion: reduce)');
        const animations = [];
        let trace;
        const process = this.el.querySelector('.process');
        if (process) {
            trace = document.createElement('div');
            trace.className = 'mc-process-trace'; trace.setAttribute('aria-hidden', 'true');
            process.prepend(trace);
        }
        if (!process) return;
        const target = process;
        const observer = new IntersectionObserver(entries => {
            if (!entries.some(entry => entry.isIntersecting)) return;
            if (!reduced.matches) {
                const frames = trace ? [{transform:'scaleX(0)'}, {transform:'scaleX(1)'}] : [{clipPath:'inset(0 12%)',opacity:.8}, {clipPath:'inset(0)',opacity:1}];
                animations.push((trace || target).animate(frames, {duration:trace ? 900 : 700, easing:'cubic-bezier(.23,1,.32,1)'}));
            }
            observer.disconnect();
        }, {threshold:.25});
        observer.observe(target);
        this.addListener(reduced, 'change', () => { if (reduced.matches) animations.forEach(animation => animation.cancel()); });
        this.registerCleanup(() => { observer.disconnect(); animations.forEach(animation => animation.cancel()); trace?.remove(); });
    }
}
registry.category('public.interactions').add('torrepulia.campaign.design', CampaignDesign);

export class BottleScrollPortrait extends Interaction {
    static selector = '.tp-cinematic .bottle-portrait';
    start() {
        const image = this.el.querySelector('img');
        const reduced = matchMedia('(prefers-reduced-motion: reduce)');
        let frame = 0;
        let disposed = false;
        const clamp = value => Math.min(1, Math.max(0, value));
        const render = () => {
            frame = 0;
            if (disposed || reduced.matches || !image) {
                if (image) image.style.transform = '';
                return;
            }
            const rect = this.el.getBoundingClientRect();
            const vh = window.innerHeight || document.documentElement.clientHeight;
            const progress = clamp((vh - rect.top) / (vh + rect.height));
            const entrance = clamp(progress / .55);
            const eased = 1 - Math.pow(1 - entrance, 3);
            const rotate = -7 + eased * 7 + Math.max(0, progress - .55) * 6;
            const lift = 100 * (1 - eased) - Math.max(0, progress - .55) * 100;
            image.style.transform = `translate3d(0, ${lift.toFixed(2)}px, 0) rotate(${rotate.toFixed(2)}deg)`;
        };
        const request = () => {
            if (!frame) frame = requestAnimationFrame(render);
        };
        this.addListener(window, 'scroll', request, { passive: true });
        this.addListener(window, 'resize', request);
        this.addListener(reduced, 'change', request);
        request();
        this.registerCleanup(() => {
            disposed = true;
            if (frame) cancelAnimationFrame(frame);
            if (image) image.style.transform = '';
        });
    }
}
registry.category('public.interactions').add('torrepulia.bottle.scroll_portrait', BottleScrollPortrait);

export class OliveOilChapters extends Interaction {
    static selector = '.tp-cinematic .family-heading h2, .tp-cinematic .regina h2 em, .tp-cinematic .mc-oil-finale';
    start() {
        const reduced = matchMedia('(prefers-reduced-motion: reduce)');
        const finale = this.el.classList.contains('mc-oil-finale');
        let line;
        if (!finale) {
            line = document.createElement('span');
            line.className = this.el.tagName === 'EM' ? 'mc-oil-underline' : 'mc-oil-thread';
            line.setAttribute('aria-hidden', 'true');
            this.el.tagName === 'EM' ? this.el.append(line) : this.el.prepend(line);
        }
        let frame = 0;
        const render = () => {
            frame = 0;
            const rect = this.el.getBoundingClientRect();
            const progress = reduced.matches ? 1 : Math.min(1, Math.max(0, (innerHeight * .88 - rect.top) / (innerHeight * .3)));
            if (line) line.style.transform = `scaleX(${progress.toFixed(4)})`;
            if (finale) {
                this.el.style.opacity = (.35 + .65 * progress).toFixed(3);
                this.el.style.transform = `translate3d(0,${(8 * (1 - progress)).toFixed(2)}px,0)`;
            }
        };
        const request = () => { if (!frame) frame = requestAnimationFrame(render); };
        this.addListener(window, 'scroll', request, { passive: true });
        this.addListener(window, 'resize', request);
        this.addListener(reduced, 'change', request);
        request();
        this.registerCleanup(() => { cancelAnimationFrame(frame); line?.remove(); this.el.style.opacity = ''; this.el.style.transform = ''; });
    }
}
registry.category('public.interactions').add('torrepulia.oil.chapters', OliveOilChapters);

export class HeroPhotoBreathing extends Interaction {
    static selector = '.tp-cinematic .hero:not(.mc-static-hero), .tp-cinematic .territory';
    start() {
        const image = this.el.querySelector('.hero-photo, .mc-territory-photo img');
        if (!image) return;
        const reduced = matchMedia('(prefers-reduced-motion: reduce)');
        image.classList.add('mc-hero-breath');
        const button = document.createElement('button');
        button.type = 'button'; button.className = 'mc-breeze-toggle';
        button.innerHTML = `<img src="${icons}pause.svg" alt=""/>`;
        (this.el.classList.contains('territory') && !this.el.classList.contains('mc-home-closing') ? image.parentElement : this.el).append(button);
        let stopped = false;
        const sync = () => {
            this.el.classList.toggle('is-breeze-paused', stopped || reduced.matches || document.hidden);
            button.hidden = reduced.matches;
            const label = stopped ? 'Riprendi animazione' : 'Metti in pausa animazione';
            button.setAttribute('aria-label', label); button.title = label;
            button.querySelector('img').src = icons + (stopped ? 'play.svg' : 'pause.svg');
        };
        this.addListener(button, 'click', () => { stopped = !stopped; sync(); });
        this.addListener(reduced, 'change', sync);
        this.addListener(document, 'visibilitychange', sync);
        const observer = new IntersectionObserver(entries => {
            image.style.animationPlayState = entries[0].isIntersecting ? '' : 'paused';
        });
        observer.observe(this.el);
        sync();
        this.registerCleanup(() => { observer.disconnect(); image.style.animationPlayState = ''; image.classList.remove('mc-hero-breath'); button.remove(); this.el.classList.remove('is-breeze-paused'); });
    }
}
registry.category('public.interactions').add('torrepulia.hero.photo_breathing', HeroPhotoBreathing);

export class FamilyGenerations extends Interaction {
    static selector = '.tp-cinematic .mc-family-editorial';
    start() {
        const reduced = matchMedia('(prefers-reduced-motion: reduce)');
        const animations = [];
        const media = this.el.querySelector('.family-media');
        if (!media) return;
        const observer = new IntersectionObserver(entries => {
            if (!entries.some(entry => entry.isIntersecting)) return;
            if (!reduced.matches) {
                const targets = [this.el.querySelector('.family-today'), this.el.querySelector('.family-archive'), this.el.querySelector('.mc-family-imprint')];
                targets.forEach((target, index) => {
                    if (!target) return;
                    animations.push(target.animate([
                        { opacity: .65, transform: `translate3d(0,${index ? 30 : 18}px,0)` },
                        { opacity: 1, transform: 'translate3d(0,0,0)' },
                    ], { duration: 800, delay: index * 120, easing: 'cubic-bezier(.23,1,.32,1)' }));
                });
            }
            observer.disconnect();
        }, { threshold: .18 });
        observer.observe(media);
        this.addListener(reduced, 'change', () => { if (reduced.matches) animations.forEach(animation => animation.cancel()); });
        this.registerCleanup(() => { observer.disconnect(); animations.forEach(animation => animation.cancel()); });
    }
}
registry.category('public.interactions').add('torrepulia.family.generations', FamilyGenerations);

export class PeranzanaEditorial extends Interaction {
    static selector = '.tp-cinematic .mc-peranzana-editorial';
    start() {
        const reduced = matchMedia('(prefers-reduced-motion: reduce)');
        const animations = [];
        const observer = new IntersectionObserver(entries => {
            for (const entry of entries) {
                if (!entry.isIntersecting) continue;
                if (!reduced.matches) {
                    const botanical = entry.target.classList.contains('mc-botanical-plate');
                    animations.push(entry.target.animate([
                        { opacity: .7, transform: botanical ? 'translateY(20px) rotate(-4deg)' : 'translateY(28px)' },
                        { opacity: 1, transform: 'none' },
                    ], { duration: 850, easing: 'cubic-bezier(.23,1,.32,1)' }));
                }
                observer.unobserve(entry.target);
            }
        }, { threshold: .2 });
        this.el.querySelectorAll('.peranzana-image, .mc-botanical-plate').forEach(target => observer.observe(target));
        this.addListener(reduced, 'change', () => { if (reduced.matches) animations.forEach(animation => animation.cancel()); });
        this.registerCleanup(() => { observer.disconnect(); animations.forEach(animation => animation.cancel()); });
    }
}
registry.category('public.interactions').add('torrepulia.peranzana.editorial', PeranzanaEditorial);

export class PugliaMapReveal extends Interaction {
    static selector = '.tp-cinematic .mc-territory-map';
    start() {
        const reduced = matchMedia('(prefers-reduced-motion: reduce)');
        const animations = [];
        const svg = this.el.querySelector('svg');
        if (!svg) return;
        const observer = new IntersectionObserver(entries => {
            if (!entries.some(entry => entry.isIntersecting)) return;
            if (!reduced.matches) {
                animations.push(svg.animate([
                    { opacity: .65, transform: 'translate3d(0,24px,0) scale(.96)' },
                    { opacity: 1, transform: 'translate3d(0,0,0) scale(1)' },
                ], { duration: 1000, easing: 'cubic-bezier(.23,1,.32,1)' }));
                const outline = svg.querySelector('.mc-map-outline');
                const length = outline.getTotalLength();
                animations.push(outline.animate([
                    { strokeDasharray: `${length}`, strokeDashoffset: `${length}` },
                    { strokeDasharray: `${length}`, strokeDashoffset: '0' },
                ], { duration: 1500, easing: 'cubic-bezier(.23,1,.32,1)' }));
                for (const selector of ['.mc-map-marker', '.mc-map-label', '.mc-map-leader']) {
                    animations.push(svg.querySelector(selector).animate([{ opacity: .15 }, { opacity: 1 }],
                        { duration: 700, delay: 350, easing: 'cubic-bezier(.23,1,.32,1)' }));
                }
            }
            observer.disconnect();
        }, { threshold: .25 });
        observer.observe(this.el);
        this.addListener(reduced, 'change', () => { if (reduced.matches) animations.forEach(animation => animation.cancel()); });
        this.registerCleanup(() => { observer.disconnect(); animations.forEach(animation => animation.cancel()); });
    }
}
registry.category('public.interactions').add('torrepulia.map.puglia', PugliaMapReveal);
