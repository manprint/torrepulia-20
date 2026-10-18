import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import { rpc } from '@web/core/network/rpc';

let instance = 0;
export class CinematicMedia extends Interaction {
    static selector = '.tp-cinematic img[src*="/static/src/cinematic/images/"]';
    start() {
        const match=this.el.getAttribute('src').match(/\/(uliveto-hero|harvest|culinary-campaign|family-archive|family-today|territory)-\d+\.webp$/);
        if(!match)return;
        const widths={'uliveto-hero':[640,1280,1920],harvest:[640,1280,1440],'culinary-campaign':[640,1280,1536],'family-archive':[640,690],'family-today':[640,690],territory:[640,1080]}[match[1]];
        const original={srcset:this.el.getAttribute('srcset'),sizes:this.el.getAttribute('sizes')};
        const base=this.el.getAttribute('src').slice(0,match.index+1);
        this.el.srcset=widths.map(w=>`${base}${match[1]}-${w}.webp ${w}w`).join(', ');
        this.el.sizes=['uliveto-hero','culinary-campaign'].includes(match[1])?'100vw':'(max-width: 760px) 100vw, 50vw';
        this.registerCleanup(()=>{for(const [key,value] of Object.entries(original)){if(value===null)this.el.removeAttribute(key);else this.el.setAttribute(key,value);}});
    }
}
registry.category('public.interactions').add('torrepulia.media',CinematicMedia);
export class CinematicCommerce extends Interaction {
    static selector = '.tp-cinematic .mc-section:has(.mc-catalog, .mc-promoted)';
    editing = false;
    async willStart() {
        let records;
        try { records = JSON.parse(this.el.dataset.productIds || '[]'); } catch { records = []; }
        try {
            this.data = await rpc('/torrepulia/formats', { ids:records.map(p => p.id), promoted:!!this.el.querySelector('.mc-promoted') });
        } catch {
            this.data = null;
        }
    }
    start() {
        const holder = this.el.querySelector('.mc-catalog, .mc-promoted');
        if (!this.data) return;
        const original = holder.innerHTML;
        holder.innerHTML = this.data.html;
        this.registerCleanup(() => { holder.innerHTML = original; });
        const prefix = `mc-formats-${++instance}`;
        const reduced=matchMedia('(prefers-reduced-motion: reduce)');
        this.registerCleanup(()=>this.selectionAnimation?.cancel());
        this.addListener(reduced,'change',()=>{if(reduced.matches)this.selectionAnimation?.cancel();});
        const options = [...holder.querySelectorAll('[data-product]')];
        if(this.el.classList.contains('mc-product-formats')){
            const list=holder.querySelector('.format-options');
            if(list){list.setAttribute('role','navigation');list.removeAttribute('aria-orientation');}
        }
        for (const button of options) {
            const id = button.dataset.product;
            if (this.el.classList.contains('mc-product-formats')) {
                const link = holder.ownerDocument.createElement('a');
                link.className=button.className;link.href=button.dataset.productUrl;link.innerHTML=button.innerHTML;
                link.dataset.product=id;link.setAttribute('aria-current',id===this.el.dataset.currentProduct?'page':'false');
                button.replaceWith(link);
                continue;
            }
            button.id = `${prefix}-${id}`;
            button.setAttribute('aria-controls', `${prefix}-panel-${id}`);
            const panel = holder.querySelector(`[data-summary="${id}"]`);
            panel.id = `${prefix}-panel-${id}`;
            panel.setAttribute('aria-labelledby', button.id);
            const select = (ev) => {
                options.forEach(b => { b.setAttribute('aria-selected', String(b === button)); b.tabIndex = b === button ? 0 : -1; });
                holder.querySelectorAll('[data-preview], [data-summary]').forEach(el => { el.hidden = (el.dataset.preview || el.dataset.summary) !== id; });
                this.selectionAnimation?.cancel();
                if (!this.editing && !reduced.matches && ev?.detail) {
                    this.selectionAnimation=holder.querySelector(`[data-preview="${id}"]`).animate([{opacity:.65,transform:'translateY(8px)'},{opacity:1,transform:'none'}],{duration:300,easing:'cubic-bezier(.23,1,.32,1)'});
                }
            };
            this.addListener(button, 'click', select);
            this.addListener(button, 'keydown', ev => {
                if (['ArrowDown','ArrowUp','Home','End'].includes(ev.key)) {
                    ev.preventDefault(); const i = options.indexOf(button);
                    const target = options[ev.key === 'Home' ? 0 : ev.key === 'End' ? options.length-1 : (i+(ev.key === 'ArrowDown' ? 1 : -1)+options.length)%options.length];
                    target.click(); target.focus();
                }
            });
        }
    }
}
registry.category('public.interactions').add('torrepulia.commerce', CinematicCommerce);
class CinematicCommerceEdit extends CinematicCommerce { editing=true; }
registry.category('public.interactions.edit').add('torrepulia.commerce', { Interaction:CinematicCommerceEdit });

export class CinematicEditorial extends Interaction {
    static selector = '.tp-cinematic .mc-section';
    start() {
        const reduced = matchMedia('(prefers-reduced-motion: reduce)');
        const animations = [];
        this.registerCleanup(() => animations.forEach(a => a.cancel()));
        this.addListener(reduced, 'change', () => { if (reduced.matches) animations.forEach(a => a.cancel()); });
        const animate = (el, frames, duration=700) => {
            if (el && !reduced.matches) animations.push(el.animate(frames,{duration,easing:'cubic-bezier(.23,1,.32,1)'}));
        };
        if (this.el.classList.contains('hero') && !this.el.classList.contains('mc-static-hero')) animate(this.el.querySelector('.hero-copy'),[{opacity:.65,transform:'translateY(16px)'},{opacity:1,transform:'none'}],800);
        const family = this.el.querySelector('.family-today');
        if (family && !this.el.classList.contains('mc-family-editorial')) {
            const observer = new IntersectionObserver(entries => { if (entries.some(e=>e.isIntersecting)) { animate(family,[{clipPath:'inset(12% 0 0)'},{clipPath:'inset(0)'}]); observer.disconnect(); } },{threshold:.2});
            observer.observe(family); this.registerCleanup(()=>observer.disconnect());
        }
        const photo = this.el.querySelector('.peranzana-image > img');
        if (photo && !this.el.classList.contains('mc-peranzana-editorial') && !this.el.querySelector('video[data-photo-film]')) {
            const update = () => {
                const rect = this.el.getBoundingClientRect();
                const mobile = innerWidth <= 760;
                if (this.el.classList.contains('hero')) photo.style.transform = reduced.matches || mobile ? 'none' : `translateY(${Math.max(0,Math.min(65,-rect.top*.08))}px) scale(1.04)`;
                else photo.style.clipPath = reduced.matches || mobile ? 'none' : `inset(0 ${Math.max(0,Math.min(7,rect.top/innerHeight*7))}%)`;
            };
            this.addListener(window,'scroll',update,{passive:true}); this.addListener(window,'resize',update); this.addListener(reduced,'change',update); update();
            this.registerCleanup(()=>{ photo.style.transform=''; photo.style.clipPath=''; });
        }
        const tabs = [...this.el.querySelectorAll('[data-sensory]')];
        tabs.forEach((tab,index) => {
            const panel = this.el.querySelector(`[data-panel="${tab.dataset.sensory}"]`);
            const originals=[[tab,'id'],[tab,'aria-controls'],[panel,'id'],[panel,'aria-labelledby']].map(([node,key])=>[node,key,node.getAttribute(key)]);
            this.registerCleanup(()=>{for(const [node,key,value] of originals){if(value===null)node.removeAttribute(key);else node.setAttribute(key,value);}});
            const prefix=`mc-sensory-${++instance}`;
            tab.id=prefix; panel.id=prefix+'-panel';tab.setAttribute('aria-controls',panel.id);panel.setAttribute('aria-labelledby',tab.id);
            this.addListener(tab,'click',ev=>{
                const changed = tab.getAttribute('aria-selected') !== 'true';
                tabs.forEach(t=>{t.setAttribute('aria-selected',String(t===tab));t.tabIndex=t===tab?0:-1;});
                this.el.querySelectorAll('[data-panel]').forEach(p=>p.hidden=p!==panel);
                if (changed && ev.detail && this.el.classList.contains('mc-peranzana-editorial')) {
                    this.sensoryAnimation?.cancel();
                    if (!reduced.matches) {
                        this.sensoryAnimation = panel.animate([{opacity:.65,transform:'translateY(8px)'},{opacity:1,transform:'none'}],{duration:280,easing:'cubic-bezier(.23,1,.32,1)'});
                    }
                }
            });
            this.addListener(tab,'keydown',ev=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(ev.key)){ev.preventDefault();const n=ev.key==='Home'?0:ev.key==='End'?tabs.length-1:(index+(ev.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;tabs[n].click();tabs[n].focus();}});
        });
        this.registerCleanup(()=>this.sensoryAnimation?.cancel());
        this.addListener(reduced,'change',()=>{if(reduced.matches)this.sensoryAnimation?.cancel();});
    }
}
registry.category('public.interactions').add('torrepulia.editorial', CinematicEditorial);

export class CinematicEditorialEdit extends Interaction {
    static selector = '.tp-cinematic .mc-section';
    start() {
        this.el.querySelectorAll('.mc-sensory-panel').forEach(panel => {
            const hidden=panel.hidden;panel.hidden=false;
            this.registerCleanup(()=>{panel.hidden=hidden;});
        });
    }
}
registry.category('public.interactions.edit').add('torrepulia.editorial.edit', { Interaction:CinematicEditorialEdit });
