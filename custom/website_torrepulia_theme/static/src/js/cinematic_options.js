import { BaseOptionComponent } from '@html_builder/core/base_option_component';
import { registry } from '@web/core/registry';
import { Plugin } from '@html_editor/plugin';
export class CinematicProductsOption extends BaseOptionComponent {
    static id = 'cinematic_products_option';
    static template = 'website_torrepulia_theme.CinematicProductsOption';
}
registry.category('website-options').add(CinematicProductsOption.id, CinematicProductsOption);

export class CinematicSavePlugin extends Plugin {
    static id = 'cinematicSave';
    resources = { clean_for_save_processors: this.clean.bind(this) };
    clean(root) {
        for (const holder of root.querySelectorAll('.mc-catalog, .mc-promoted')) {
            const link = root.ownerDocument.createElement('a');
            link.href = '/shop'; link.className = 'button dark'; link.textContent = 'Scopri La Regina';
            holder.replaceChildren(link);
        }
        const sections=[...root.querySelectorAll('.mc-section')];
        if(root.matches('.mc-section'))sections.unshift(root);
        for (const section of sections) {
            section.querySelectorAll('.mc-sensory-panel').forEach((panel,i)=>panel.hidden=i!==0);
            section.querySelectorAll('[data-sensory]').forEach((tab,i)=>{tab.setAttribute('aria-selected',String(i===0));tab.tabIndex=i===0?0:-1;});
        }
        return root;
    }
}
registry.category('website-plugins').add(CinematicSavePlugin.id, CinematicSavePlugin);
