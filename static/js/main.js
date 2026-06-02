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
});

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
		window.closeModal();
	}
});
