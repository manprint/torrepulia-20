import { registry } from '@web/core/registry';
import { RequestSelectionStore } from './request_store';

registry.category('services').add('torrepulia.request', {
    start() {
        let channel;
        let storage;
        try {
            storage = window.sessionStorage;
        } catch {
            // Storage is optional.
        }
        try {
            channel = new BroadcastChannel('torrepulia-request');
        } catch {
            // Cross-tab notifications are optional.
        }
        const store = new RequestSelectionStore({
            storage,
            onChanged: () => channel?.postMessage({ changed: true }),
            transport: async (kind, payload, csrfToken) => {
                const response = await fetch(kind === 'read' ? '/torrepulia/request/current' : '/torrepulia/request/update', {
                    method: kind === 'read' ? 'GET' : 'POST', credentials: 'same-origin', cache: 'no-store',
                    headers: kind === 'read' ? {} : { 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8' },
                    body: kind === 'read' ? undefined : new URLSearchParams({
                        csrf_token: csrfToken, payload: JSON.stringify(payload),
                    }),
                });
                if (response.status >= 500 || response.status === 400 || !response.headers.get('content-type')?.includes('application/json')) {
                    throw new Error('Selection transport failed');
                }
                return response.json();
            },
        });
        const refresh = () => {
            if (store.state) {
                store.read().catch(() => {});
            }
        };
        window.addEventListener('pageshow', refresh);
        window.addEventListener('focus', refresh);
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                refresh();
            }
        });
        if (channel) {
            channel.onmessage = refresh;
        }
        return store;
    },
});
