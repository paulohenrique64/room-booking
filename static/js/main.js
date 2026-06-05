document.addEventListener('DOMContentLoaded', () => {
	if (window.htmx) {
		window.htmx.on('htmx:configRequest', (event) => {
			const tokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
			if (tokenInput) {
				event.detail.headers['X-CSRFToken'] = tokenInput.value;
			}
		});

	}

	const sidebarLinks = document.querySelectorAll('[data-nav-link]');
	const currentPath = window.location.pathname;

	sidebarLinks.forEach((link) => {
		const href = link.getAttribute('href') || '';
		if (href && currentPath.startsWith(href)) {
			link.classList.add('is-active');
		} else {
			link.classList.remove('is-active');
		}
	});

	const toggleButton = document.getElementById('sidebar-toggle');
	const sidebar = document.getElementById('sidebar');

	if (toggleButton && sidebar) {
		toggleButton.addEventListener('click', () => {
			sidebar.classList.toggle('hidden');
		});
	}

	const searchInput = document.querySelector('[data-search-input]');
	if (searchInput) {
		searchInput.addEventListener('input', (event) => {
			const query = event.target.value.toLowerCase().trim();
			filterSearchResults(query);
		});
	}

	document.addEventListener('click', (event) => {
		const toggle = event.target.closest('[data-notifications-toggle]');
		const activeRoot = document.querySelector('[data-notifications-root]');
		if (toggle && activeRoot) {
			event.stopPropagation();
			const panel = activeRoot.querySelector('[data-notifications-panel]');
			const isOpen = !panel.classList.contains('hidden');
			panel.classList.toggle('hidden', isOpen);
			toggle.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
			return;
		}

		if (activeRoot && !activeRoot.contains(event.target)) {
			closeNotificationsPanel(activeRoot);
		}
	});

	document.addEventListener('keydown', (event) => {
		if (event.key === 'Escape' || event.key === 'Esc') {
			const activeRoot = document.querySelector('[data-notifications-root]');
			if (activeRoot) closeNotificationsPanel(activeRoot);
		}
	});
});

document.addEventListener('click', (event) => {
	const trigger = event.target.closest('[data-delete-confirm]');
	if (!trigger || trigger.tagName === 'FORM') return;

	event.preventDefault();
	event.stopPropagation();
	event.stopImmediatePropagation();

	openDeleteConfirmDialog({
		message: trigger.getAttribute('data-delete-confirm'),
		onConfirm: () => {
			trigger.removeAttribute('data-delete-confirm');
			trigger.click();
		},
	});
}, true);

document.addEventListener('submit', (event) => {
	const form = event.target.closest('form[data-delete-confirm]');
	if (!form) return;

	event.preventDefault();
	event.stopPropagation();
	event.stopImmediatePropagation();

	openDeleteConfirmDialog({
		message: form.getAttribute('data-delete-confirm'),
		onConfirm: () => {
			form.removeAttribute('data-delete-confirm');
			form.requestSubmit();
		},
	});
}, true);

document.addEventListener('modalClosed', () => {
	window.closeModal();
});

function filterSearchResults(query) {
	const searchableItems = document.querySelectorAll('[data-search-name]');
	searchableItems.forEach((item) => {
		const name = (item.getAttribute('data-search-name') || '').toLowerCase();
		if (!query || name.includes(query)) {
			item.style.display = '';
		} else {
			item.style.display = 'none';
		}
	});
}

function closeNotificationsPanel(root) {
	const panel = root.querySelector('[data-notifications-panel]');
	const toggle = root.querySelector('[data-notifications-toggle]');
	if (!panel || !toggle) return;
	panel.classList.add('hidden');
	toggle.setAttribute('aria-expanded', 'false');
}

function openDeleteConfirmDialog({ message, onConfirm }) {
	closeDeleteConfirmDialog();

	const overlay = document.createElement('div');
	overlay.id = 'delete-confirm-overlay';
	overlay.className = 'fixed inset-0 z-[120] flex items-center justify-center bg-[rgba(18,28,42,0.36)] p-4 backdrop-blur-md';
	overlay.innerHTML = `
		<div class="w-full max-w-md overflow-hidden rounded-2xl border border-outline-variant bg-surface-card shadow-xl" data-delete-confirm-dialog>
			<div class="flex items-start gap-4 border-b border-outline-variant bg-surface px-6 py-5">
				<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-error-container text-on-error-container">
					<span class="material-symbols-outlined text-[22px]">delete</span>
				</div>
				<div>
					<h2 class="text-sm font-extrabold tracking-tight text-on-surface">Confirmar exclusão</h2>
					<p class="mt-1 text-xs font-medium leading-5 text-on-surface-variant">${escapeHtml(message)}</p>
				</div>
			</div>
			<div class="flex flex-col-reverse gap-3 px-6 py-5 sm:flex-row sm:justify-end">
				<button type="button" class="rounded-xl border border-outline-variant px-5 py-2.5 text-sm font-semibold text-on-surface-variant transition hover:bg-outline-variant/30" data-delete-confirm-cancel>Cancelar</button>
				<button type="button" class="rounded-xl bg-error-base px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:brightness-95" data-delete-confirm-accept>Excluir</button>
			</div>
		</div>
	`;

	document.body.appendChild(overlay);

	overlay.querySelector('[data-delete-confirm-cancel]').addEventListener('click', closeDeleteConfirmDialog);
	overlay.querySelector('[data-delete-confirm-accept]').addEventListener('click', () => {
		closeDeleteConfirmDialog();
		onConfirm();
	});
	overlay.addEventListener('click', (event) => {
		if (event.target === overlay) closeDeleteConfirmDialog();
	});
}

function closeDeleteConfirmDialog() {
	const overlay = document.getElementById('delete-confirm-overlay');
	if (overlay) overlay.remove();
}

function escapeHtml(value) {
	return String(value)
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&#039;');
}

// Modal helpers used by HTMX-injected modal content
window.closeModal = function() {
	const container = document.getElementById('modal-container');
	if (container) container.innerHTML = '';
	// Some front-end templates may inject an inner element id; clear it as well for safety
	const inner = document.getElementById('modal-container-elem');
	if (inner && inner.parentNode) inner.parentNode.removeChild(inner);
};

document.addEventListener('click', function(event) {
    const target = event.target;

    // Clique direto no fundo escuro do overlay
    if (target.id === 'modal-overlay') {
        window.closeModal();
        return;
    }

    // Botões explicitamente marcados para fechar
    if (target.closest('.modal-close') || target.closest('[data-modal-close]')) {
        window.closeModal();
        return;
    }
});

// Close modal on Escape key
document.addEventListener('keydown', function(event) {
	if (event.key === 'Escape' || event.key === 'Esc') {
		closeDeleteConfirmDialog();
		window.closeModal();
	}
});
