/** @odoo-module **/

// Framework-independent state machine: only server responses change quantities.
export class SelectionError extends Error {
    constructor(code, message) {
        super(message);
        this.code = code;
    }
}

function immutable(value) {
    if (value && typeof value === 'object') {
        Object.values(value).forEach(immutable);
        Object.freeze(value);
    }
    return value;
}

export class RequestSelectionStore {
    constructor({ transport, makeId = () => crypto.randomUUID(), storage = null, onChanged = () => {} }) {
        this.transport = transport;
        this.makeId = makeId;
        this.storage = storage;
        this.onChanged = onChanged;
        this.state = null;
        this.pending = null;
        this.listeners = new Set();
        this.queue = Promise.resolve();
        this.ticket = 0;
        this.acceptedTicket = 0;
    }

    subscribe(callback) {
        this.listeners.add(callback);
        if (this.state) {
            try {
                callback(this.state);
            } catch {
                // Subscriber failures do not alter the shared state.
            }
        }
        return () => this.listeners.delete(callback);
    }

    _enqueue(work) {
        const task = this.queue.then(work);
        this.queue = task.catch(() => {});
        return task;
    }

    _accept(state, ticket) {
        if (!state || ticket < this.acceptedTicket || (this.state &&
            state.selection_id === this.state.selection_id && state.revision < this.state.revision)) {
            return false;
        }
        this.acceptedTicket = ticket;
        this.state = immutable(structuredClone(state));
        for (const listener of this.listeners) {
            try {
                listener(this.state);
            } catch {
                // One consumer must not prevent other surfaces from updating.
            }
        }
        return true;
    }

    _storageKey() {
        return `torrepulia.request.pending.${this.state.website_id}`;
    }

    _savePending() {
        try {
            if (this.pending) {
                this.storage?.setItem(this._storageKey(), JSON.stringify(this.pending));
            } else {
                this.storage?.removeItem(this._storageKey());
            }
        } catch {
            // Disabled storage must not prevent server-backed selection.
        }
    }

    async _read() {
        const ticket = ++this.ticket;
        const response = await this.transport('read');
        this.csrfToken = response.csrf_token;
        this._accept(response.state, ticket);
        if (!this.pending) {
            try {
                this.pending = JSON.parse(this.storage?.getItem(this._storageKey()) || 'null');
            } catch {
                this.pending = null;
            }
        }
        return this.state;
    }

    read() {
        if (!this.readTask) {
            const task = this._enqueue(() => this._read());
            this.readTask = task;
            task.finally(() => {
                if (this.readTask === task) {
                    this.readTask = null;
                }
            }).catch(() => {});
        }
        return this.readTask;
    }

    async _sendPending() {
        const ticket = ++this.ticket;
        let response;
        // Both attempts carry exactly the same operation_id and semantic body.
        for (let attempt = 0; attempt < 2; attempt++) {
            try {
                response = await this.transport('write', this.pending, this.csrfToken);
                break;
            } catch (error) {
                if (attempt === 1) {
                    throw new SelectionError('network', 'network');
                }
                // Refresh CSRF after a login/session rotation. Keep the pending ID.
                await this._read();
            }
        }
        this._accept(response.state, Math.max(ticket, this.acceptedTicket));
        this.pending = null;
        this._savePending();
        if (!response.ok) {
            throw new SelectionError(response.code, response.message || response.code);
        }
        this.onChanged();
        return this.state;
    }

    _mutate(operation, data = {}) {
        return this._enqueue(async () => {
            if (!this.state) {
                await this._read();
            }
            if (!this.state.enabled) {
                throw new SelectionError('disabled', 'disabled');
            }
            if (this.pending) {
                throw new SelectionError('pending', 'pending');
            }
            this.pending = { ...data, operation, operation_id: this.makeId(),
                selection_id: this.state.selection_id, revision: this.state.revision };
            this._savePending();
            return this._sendPending();
        });
    }

    retryPending() {
        return this._enqueue(async () => {
            await this._read();
            return this.pending ? this._sendPending() : this.state;
        });
    }

    add(configuration, quantity = 1) {
        return this._mutate('add', { ...configuration, quantity });
    }

    setQuantity(lineKey, quantity) {
        return this._mutate('set', { line_key: lineKey, quantity });
    }

    setConfiguration(configuration, quantity) {
        return this._mutate('set_configuration', { ...configuration, quantity });
    }

    remove(lineKey) {
        return this._mutate('remove', { line_key: lineKey });
    }

    clear() {
        return this._mutate('clear');
    }

    afterSubmission() {
        return this._enqueue(async () => {
            const state = await this._read();
            this.onChanged();
            return state;
        });
    }
}
