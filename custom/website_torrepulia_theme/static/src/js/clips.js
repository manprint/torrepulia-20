import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';

const base = '/website_torrepulia_theme/static/src/cinematic/clips/';
const icons = '/website_torrepulia_theme/static/src/cinematic/icons/';

/**
 * A photo that comes alive: the page keeps the clip's first frame as an ordinary image
 * (data-tp-clip names the clip), and here it becomes a muted loop while it is on screen.
 * The image stays for reduced motion, data saving, the Builder, and when the owner swaps it.
 */
export class Clip extends Interaction {
    static selector = 'img[data-tp-clip]';
    start() {
        const name = this.el.dataset.tpClip;
        if (!/^[a-z-]+$/.test(name) || this.el.getAttribute('src') !== `${base}${name}-poster.webp`) return;
        const reduced = matchMedia('(prefers-reduced-motion: reduce)');
        if (reduced.matches || navigator.connection?.saveData) return;
        const image = this.el;
        // The frame takes the photo's classes, so the page lays it out exactly like the photo.
        const frame = document.createElement('span');
        frame.className = `${image.className} tp-clip`;
        const video = document.createElement('video');
        Object.assign(video, { muted: true, loop: true, playsInline: true, preload: 'none', poster: image.getAttribute('src') });
        video.setAttribute('aria-hidden', 'true');
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'tp-clip-toggle';
        button.innerHTML = '<img alt="" width="16" height="16"/>';
        frame.append(video, button);
        image.replaceWith(frame);
        let visible = false;
        let stopped = false;
        const sync = () => {
            const label = video.paused ? 'Riproduci il video' : 'Metti in pausa il video';
            button.setAttribute('aria-label', label);
            button.title = label;
            button.querySelector('img').src = icons + (video.paused ? 'play.svg' : 'pause.svg');
        };
        const update = async () => {
            if (stopped || !visible || document.hidden || reduced.matches) {
                video.pause();
            } else {
                if (!video.getAttribute('src')) video.src = `${base}${name}.mp4`;
                try { await video.play(); } catch { /* The first frame stays if autoplay is refused. */ }
            }
            sync();
        };
        const observer = new IntersectionObserver(entries => { visible = entries[0].isIntersecting; update(); }, { threshold: .2 });
        observer.observe(frame);
        this.addListener(video, 'play', sync);
        this.addListener(video, 'pause', sync);
        this.addListener(button, 'click', () => { stopped = !video.paused; update(); });
        this.addListener(reduced, 'change', update);
        this.addListener(document, 'visibilitychange', update);
        sync();
        this.registerCleanup(() => {
            observer.disconnect();
            video.pause();
            video.removeAttribute('src');
            video.load();
            frame.replaceWith(image);
        });
    }
}
registry.category('public.interactions').add('torrepulia.clip', Clip);
