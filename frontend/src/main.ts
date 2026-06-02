import './index.css';
// @ts-ignore
import htmx from 'htmx.org';

// Bind htmx to window globally
(window as any).htmx = htmx;

// Declare functions on window for easy access in HTML template triggers
declare global {
  interface Window {
    closeModal: () => void;
    selectRoomInModal: (roomId: string) => void;
    toggleEquipmentInModal: (element: HTMLElement) => void;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  console.log('Workspace Portal UI loaded successfully with HTMX.');

  // 1. Search filter functionality (real-time filtering of workspace components)
  const searchInput = document.querySelector('input[placeholder="Search rooms..."]') as HTMLInputElement;
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const query = (e.target as HTMLInputElement).value.toLowerCase().trim();
      filterWorkspaceCards(query);
    });
  }

  // 2. Automated Sidebar Class Toggles based on HTMX view navigation
  document.addEventListener('htmx:afterSwap', (event: Event) => {
    const customEvent = event as CustomEvent;
    const xhrPath = customEvent.detail?.pathInfo?.requestPath || '';
    
    if (xhrPath.includes('/api/views/')) {
      const viewName = xhrPath.split('/api/views/')[1]?.split('?')[0];
      if (viewName) {
        updateActiveSidebarItem(viewName);
      }
    }
  });
});

/**
 * Highlighting active layout classes on navigation items
 */
function updateActiveSidebarItem(viewName: string) {
  const sidebarLinks = document.querySelectorAll('aside nav a');
  sidebarLinks.forEach((link) => {
    const hrefAttr = link.getAttribute('hx-get');
    if (hrefAttr && hrefAttr.includes(viewName)) {
      // Active styling
      link.classList.add('text-primary', 'font-semibold', 'bg-primary-container/10');
      link.classList.remove('text-on-surface-variant', 'hover:bg-surface-container');
      const icon = link.querySelector('.material-symbols-outlined');
      if (icon) icon.classList.add('symbol-filled');
    } else {
      // Non-active styling
      link.classList.remove('text-primary', 'font-semibold', 'bg-primary-container/10');
      link.classList.add('text-on-surface-variant', 'hover:bg-surface-container');
      const icon = link.querySelector('.material-symbols-outlined');
      if (icon) icon.classList.remove('symbol-filled');
    }
  });
}

/**
 * Real-time filter matching for rooms, schedules, and cards
 */
function filterWorkspaceCards(query: string) {
  // Filters Rooms in the Dashboard Schedule Rows
  const scheduleRows = document.querySelectorAll('.calendar-track .space-y-4 > .flex');
  scheduleRows.forEach((row) => {
    const roomNameEl = row.querySelector('.font-body-md');
    if (roomNameEl) {
      const roomName = roomNameEl.textContent?.toLowerCase() || '';
      const parentRow = row as HTMLElement;
      if (roomName.includes(query) || query === '') {
        parentRow.style.display = 'flex';
      } else {
        parentRow.style.display = 'none';
      }
    }
  });

  // Filters Available Rooms Cards
  const roomCards = document.querySelectorAll('#rooms-list-container .bento-card');
  roomCards.forEach((card) => {
    const h4El = card.querySelector('h4');
    if (h4El) {
      const roomName = h4El.textContent?.toLowerCase() || '';
      const parentCard = card as HTMLElement;
      if (roomName.includes(query) || query === '') {
        parentCard.style.display = 'flex';
      } else {
        parentCard.style.display = 'none';
      }
    }
  });

  // Filters Equipment Items
  const equipmentItems = document.querySelectorAll('#equipment-list-container li');
  equipmentItems.forEach((li) => {
    const nameEl = li.querySelector('.font-body-lg');
    if (nameEl) {
      const equipName = nameEl.textContent?.toLowerCase() || '';
      const parentLi = li as HTMLElement;
      if (equipName.includes(query) || query === '') {
        parentLi.style.display = 'flex';
      } else {
        parentLi.style.display = 'none';
      }
    }
  });
}

/**
 * Handle elegant Close Modal Animations before deleting DOM nodes
 */
window.closeModal = function () {
  const modalOverlay = document.getElementById('modal-overlay');
  const modalContainer = document.getElementById('modal-container-elem');
  
  if (modalOverlay && modalContainer) {
    // Apply fade-out / zoom-out keyframes by replacing classes
    modalOverlay.style.transition = 'opacity 0.2s ease-out';
    modalOverlay.style.opacity = '0';
    
    modalContainer.style.transition = 'all 0.2s ease-out';
    modalContainer.style.opacity = '0';
    modalContainer.style.transform = 'scale(0.95)';
    
    setTimeout(() => {
      const rootModalContainer = document.getElementById('modal-container');
      if (rootModalContainer) {
        rootModalContainer.innerHTML = '';
      }
    }, 200);
  } else {
    // Fallback if structured divs are missing
    const rootModalContainer = document.getElementById('modal-container');
    if (rootModalContainer) rootModalContainer.innerHTML = '';
  }
};

/**
 * Handle custom room selecting in the modal creation window
 */
window.selectRoomInModal = function(roomId: string) {
  const cards = document.querySelectorAll('[data-room-card]');
  cards.forEach((card) => {
    const cardElement = card as HTMLElement;
    const isTarget = cardElement.getAttribute('data-room-card') === roomId;
    const checkBadge = cardElement.querySelector('.check-badge-container') as HTMLElement;
    const roomIconContainer = cardElement.querySelector('.room-icon-container') as HTMLElement;
    
    // Hidden radio/input synchronizer
    const input = cardElement.querySelector('input[type="radio"]') as HTMLInputElement;

    if (isTarget) {
      cardElement.classList.remove('border-outline-variant', 'border');
      cardElement.classList.add('border-2', 'border-primary-base');
      if (checkBadge) checkBadge.style.display = 'flex';
      if (roomIconContainer) {
        roomIconContainer.classList.remove('bg-surface-container');
        roomIconContainer.classList.add('bg-primary-container/20', 'text-primary-base');
      }
      if (input) input.checked = true;
    } else {
      cardElement.classList.remove('border-2', 'border-primary-base');
      cardElement.classList.add('border', 'border-outline-variant');
      if (checkBadge) checkBadge.style.display = 'none';
      if (roomIconContainer) {
        roomIconContainer.classList.add('bg-surface-container');
        roomIconContainer.classList.remove('bg-primary-container/20', 'text-primary-base');
      }
      if (input) input.checked = false;
    }
  });
};

/**
 * Manage dynamic interactive highlights for booking equipment selection
 */
window.toggleEquipmentInModal = function(element: HTMLElement) {
  const checkbox = element.querySelector('input[type="checkbox"]') as HTMLInputElement;
  if (!checkbox) return;
  
  // Toggle checkbox state programmatically on click
  checkbox.checked = !checkbox.checked;
  
  if (checkbox.checked) {
    element.classList.remove('border-outline-variant', 'bg-surface-container-lowest', 'text-on-surface-variant');
    element.classList.add('border-2', 'border-primary-base', 'bg-primary-container/10', 'text-primary-base');
  } else {
    element.classList.add('border', 'border-outline-variant', 'bg-surface-container-lowest', 'text-on-surface-variant');
    element.classList.remove('border-2', 'border-primary-base', 'bg-primary-container/10', 'text-primary-base');
  }
};
