import express from "express";
import { createServer as createViteServer } from "vite";
import fs from "fs";
import * as pathNode from "path";

// -------------------------------------------------------------
// Database Interfaces and Definitions
// -------------------------------------------------------------
interface Room {
  id: string;
  name: string;
  capacity: number;
  status: "available" | "occupied";
  image: string;
  equipment: string[]; // references material symbol names (e.g. ['videocam', 'edit_note'])
}

interface Equipment {
  id: string;
  name: string;
  qty: number;
  icon: string; // material symbol name
}

interface Booking {
  id: string;
  title: string;
  date: string; // YYYY-MM-DD
  startTime: string; // e.g., '10:00 AM'
  endTime: string; // e.g., '11:30 AM'
  room: string; // Room name or Room ID
  equipment: string[]; // equipment items
}

// -------------------------------------------------------------
// Initial Mock In-Memory Database State
// -------------------------------------------------------------
let rooms: Room[] = [
  {
    id: "boardroom-a",
    name: "Boardroom Alpha & A",
    capacity: 12,
    status: "occupied",
    image: "https://lh3.googleusercontent.com/aida-public/AB6AXuAQB7l6M1s0CAjAyDxn43720bwv37d1PR3oLmMHwUjzevN8uaOIs48NAxlN9zueFQY-KzXNZvyQ2Fdni439Gc__o9IdF9KRgz0KmExVIrMC7o2WQCMkVl5Awkowlzawh4D0uDvwfsrn7gkE29NsDC0wHaZWvR-mqm0GZlsWIqzgJ3rMPqe0acdIULNuWfm4kigkt-sRAzS4BYLQtCV-DTD_286pfk6qDANynobRZiF7EcJpT7kqspVaatKlC3CWbjrT7fIUOCzmVpru",
    equipment: ["videocam", "edit_note", "local_cafe"]
  },
  {
    id: "huddle-1",
    name: "Huddle Room 1",
    capacity: 4,
    status: "occupied",
    image: "https://lh3.googleusercontent.com/aida-public/AB6AXuDnIjJr43gVPqmiSbt2iPaw34cOdKngWsWsETYoH029pulblFKe92WIwSMSpHIz4UIM5AxrgZYY7q3L0yn5nsqbji5XcUA7zPsL7oWJsJ_WpCLPbR0h2PFoMKbFZErBjPQzIkY695KOpVDd5-yP60zVVRc9ImQf9Qec_eMQ0X5InMkIfCtRjQPrI6_yCyqVFpOSdZMJaF3-kunYYzHNVrJsaP0tOy06H1upFiZuDT9wJvRrQhugxaW_PbpRdwCng9FRpEMcAakZG9KF",
    equipment: ["tv", "edit_note"]
  },
  {
    id: "studio-b",
    name: "Studio B",
    capacity: 8,
    status: "available",
    image: "https://lh3.googleusercontent.com/aida-public/AB6AXuAWojhQV4tHPXBwK2Eg-vjB0Kgq3iT7Sv5TmsIq92P7QXLLh772nRonO1yPvd042F2r0xx2hGSu1gxLGvRjPvs0WosoJ8mQteK3vvV40SBSK9vSYI7qfrl-OMg8TPGQDPXI-ZEoK7yKIKMpDnlml2bRsKy5pGnZ2D6GY3kWs3S-UgCGY6BN_LFRG2pBjd_4NXc4w0Nlpw89Kd-O867KHRZmT_PWabbBrBT-nZ2d1H7nrfsPpB6Ab8MPql2OsIkDaESc-kdH7SSi9HUc",
    equipment: ["videocam"]
  }
];

let equipments: Equipment[] = [
  { id: "proj", name: "4K Projector", qty: 5, icon: "videocam" },
  { id: "tv", name: "Smart TV 65\"", qty: 12, icon: "tv" },
  { id: "board", name: "Glass Whiteboard", qty: 8, icon: "edit_note" }
];

let bookings: Booking[] = [
  {
    id: "book-1",
    title: "Executive Q3 Review",
    date: "2026-05-31",
    startTime: "10:00 AM",
    endTime: "11:30 AM",
    room: "boardroom-a",
    equipment: ["videocam", "edit_note"]
  },
  {
    id: "book-2",
    title: "Sync diário focado",
    date: "2026-05-31",
    startTime: "09:00 AM",
    endTime: "10:00 AM",
    room: "huddle-1",
    equipment: ["edit_note"]
  },
  {
    id: "book-3",
    title: "Entrevistas de Contratação",
    date: "2026-05-31",
    startTime: "12:00 PM",
    endTime: "01:00 PM",
    room: "huddle-1",
    equipment: ["tv"]
  }
];

// Helper to check and reset rooms status depending on active daily bookings
function updateRoomsDynamicState() {
  rooms.forEach(room => {
    const isOccupied = bookings.some(b => {
      // Very basic match for active daily occupancy
      return b.room === room.id;
    });
    room.status = isOccupied ? "occupied" : "available";
  });
}

// -------------------------------------------------------------
// Helper math for Timeline Positions in daily calendar schedule
// -------------------------------------------------------------
function getTimeOffsets(startTime: string, endTime: string): { left: number; width: number } {
  const parseHour = (timeStr: string): number => {
    const cleanStr = timeStr.trim().toUpperCase();
    const isPM = cleanStr.includes("PM");
    const isAM = cleanStr.includes("AM");
    
    // strip out characters we don't need
    const digitsOnly = cleanStr.replace("AM", "").replace("PM", "").trim();
    let [hoursPart, minutesPart] = digitsOnly.split(":");
    let hours = parseInt(hoursPart, 10) || 0;
    const minutes = parseInt(minutesPart, 10) || 0;
    
    if (isPM && hours !== 12) hours += 12;
    if (isAM && hours === 12) hours = 0;
    
    return hours + minutes / 60;
  };

  const startHour = parseHour(startTime);
  const endHour = parseHour(endTime);
  
  // Daily timeline bounds: 09:00 AM to 04:00 PM (16:00) => 7 Hours Total span
  const timelineStart = 9.0;
  const totalTimelineHours = 7.0;
  
  const clamp = (val: number) => Math.max(0, Math.min(100, val));
  
  const leftPct = clamp(((startHour - timelineStart) / totalTimelineHours) * 100);
  const widthPct = clamp(((endHour - startHour) / totalTimelineHours) * 100);
  
  return { left: leftPct, width: widthPct };
}

// -------------------------------------------------------------
// HTML Views Renders Engines (Server-Side)
// -------------------------------------------------------------

function renderDashboard(): string {
  updateRoomsDynamicState();
  const totalRoomsCount = rooms.length;
  const occupiedCount = rooms.filter(r => r.status === "occupied").length;
  const availableCount = totalRoomsCount - occupiedCount;
  const capacityPct = totalRoomsCount > 0 ? Math.round((occupiedCount / totalRoomsCount) * 100) : 0;

  // Render upcoming meeting focus highlight element (e.g. Boardroom Q3 Review)
  const upcomingBooking = bookings[0];
  const upcomingRoom = rooms.find(r => r.id === upcomingBooking?.room) || rooms[0];

  return `
    <!-- Top Dashboard Overview -->
    <div class="flex flex-col gap-8 max-w-[1400px] mx-auto select-none">
      
      <!-- Sub-Header and Actions bar -->
      <div class="flex justify-between items-end border-b border-outline-variant pb-6">
        <div>
          <h2 class="text-2xl mt-2 md:text-3xl font-extrabold text-on-surface tracking-tight">Visão Geral</h2>
          <p class="text-sm text-on-surface-variant font-medium mt-1">Gerencie recursos de espaço corporativo e agendas de reserva em tempo real.</p>
        </div>
        <button class="bg-primary-base hover:bg-primary-light text-white text-sm font-semibold px-5 py-2.5 rounded-xl flex items-center gap-1.5 active:scale-[0.98] transition-all cursor-pointer shadow-sm shadow-primary-base/10"
                hx-get="/api/modals/create-booking"
                hx-target="#modal-container"
                hx-swap="innerHTML">
          <span class="material-symbols-outlined text-[18px]">add</span>
          Nova Reserva
        </button>
      </div>

      <!-- Bento Grid (Stats Boxes) -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-6">
        
        <!-- Total Rooms item -->
        <div class="lg:col-span-3 bento-card flex flex-col justify-between h-44">
          <div class="flex justify-between items-start">
            <span class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Total de Salas</span>
            <div class="w-8 h-8 rounded-xl bg-outline-variant/30 flex items-center justify-center text-on-surface-variant">
              <span class="material-symbols-outlined text-[20px]">meeting_room</span>
            </div>
          </div>
          <div>
            <span class="text-4xl font-extrabold text-on-surface tracking-tight">${totalRoomsCount}</span>
            <p class="text-xs text-on-surface-variant font-medium mt-1">Dispostas em 3 andares</p>
          </div>
        </div>

        <!-- Available percentage metrics -->
        <div class="lg:col-span-3 bento-card flex flex-col justify-between h-44">
          <div class="flex justify-between items-start">
            <span class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Salas Disponíveis</span>
            <div class="w-8 h-8 rounded-xl bg-secondary-container/20 flex items-center justify-center text-secondary-base">
              <span class="material-symbols-outlined text-[20px] symbol-filled">check_circle</span>
            </div>
          </div>
          <div>
            <span class="text-4xl font-extrabold text-on-surface tracking-tight">${availableCount}</span>
            <p class="text-xs text-secondary-base font-semibold mt-1 flex items-center gap-1">
              <span class="material-symbols-outlined text-[14px]">trending_up</span> Coeficiente ${capacityPct}% ocupação
            </p>
          </div>
        </div>

        <!-- Focus Spotlight: Upcoming occupied slot -->
        <div class="lg:col-span-6 bento-card relative overflow-hidden h-44">
          <div class="absolute inset-0 bg-gradient-to-r from-primary-container/20 to-transparent opacity-60 pointer-events-none"></div>
          <div class="relative z-10 flex justify-between h-full">
            <div class="flex flex-col justify-between">
              <div>
                <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-error-container text-on-error-container text-[10px] font-bold uppercase tracking-wider mb-2.5">
                  <span class="w-1.5 h-1.5 rounded-full bg-error-base animate-pulse"></span> Ocupado Agora
                </span>
                <h3 class="text-lg font-bold text-on-surface tracking-tight">${upcomingBooking ? upcomingBooking.title : "Nenhuma reunião"}</h3>
                <p class="text-xs text-on-surface-variant font-medium mt-0.5">${upcomingRoom ? upcomingRoom.name : "Nenhum espaço reservado"}</p>
              </div>
              <div class="flex items-center gap-4">
                <div class="flex items-center gap-1 text-on-surface-variant text-xs font-semibold">
                  <span class="material-symbols-outlined text-[16px]">schedule</span> 
                  ${upcomingBooking ? `${upcomingBooking.startTime} - ${upcomingBooking.endTime}` : "-"}
                </div>
                <div class="flex -space-x-1.5">
                  <div class="w-5 h-5 rounded-full bg-outline-border text-[9px] font-bold text-white flex items-center justify-center border border-white">PS</div>
                  <div class="w-5 h-5 rounded-full bg-primary-light text-[9px] font-bold text-white flex items-center justify-center border border-white">AM</div>
                  <div class="w-5 h-5 rounded-full bg-surface-dim font-bold text-[9px] text-on-surface flex items-center justify-center border border-white">+3</div>
                </div>
              </div>
            </div>
            
            ${upcomingRoom ? `
              <div class="w-24 h-24 rounded-xl overflow-hidden border border-outline-variant shadow-sm hidden sm:block">
                <img class="w-full h-full object-cover" src="${upcomingRoom.image}" alt="${upcomingRoom.name}" />
              </div>
            ` : ""}
          </div>
        </div>

      </div>

      <!-- Live Timeline Agenda Planner -->
      <div class="bento-card p-0 overflow-hidden flex flex-col mt-2">
        
        <!-- Header tools for calendar schedule -->
        <div class="px-6 py-5 border-b border-outline-variant flex justify-between items-center bg-surface-card select-none">
          <h3 class="text-sm font-bold text-on-surface tracking-tight">Grade de Reservas (Hoje)</h3>
          <div class="flex items-center gap-2">
            <button class="p-1 rounded-lg text-on-surface-variant hover:bg-outline-variant/30 cursor-pointer transition-colors">
              <span class="material-symbols-outlined">chevron_left</span>
            </button>
            <span class="text-xs font-bold text-on-surface">31 de Maio, 2026</span>
            <button class="p-1 rounded-lg text-on-surface-variant hover:bg-outline-variant/30 cursor-pointer transition-colors">
              <span class="material-symbols-outlined">chevron_right</span>
            </button>
          </div>
        </div>

        <!-- Scrollable timelines rail -->
        <div class="overflow-x-auto calendar-track flex-1 bg-surface-card relative min-h-[300px]">
          <div class="min-w-[800px] p-6 relative">
            
            <!-- Timeline Grid Time Headers (09h00 to 16h00) -->
            <div class="flex border-b border-outline-variant pb-2.5 mb-5 ml-40">
              <div class="flex-1 text-[11px] font-semibold text-on-surface-variant text-center">09:00</div>
              <div class="flex-1 text-[11px] font-semibold text-on-surface-variant text-center">10:00</div>
              <div class="flex-1 text-[11px] font-semibold text-on-surface-variant text-center">11:00</div>
              <div class="flex-1 text-[11px] font-semibold text-on-surface-variant text-center">12:00</div>
              <div class="flex-1 text-[11px] font-semibold text-on-surface-variant text-center">13:00</div>
              <div class="flex-1 text-[11px] font-semibold text-on-surface-variant text-center">14:00</div>
              <div class="flex-1 text-[11px] font-semibold text-on-surface-variant text-center">15:00</div>
            </div>

            <!-- Rooms rows rendering -->
            <div class="space-y-4">
              ${rooms.map(room => {
                const roomBookings = bookings.filter(b => b.room === room.id);
                return `
                  <div class="flex items-center relative group">
                    <!-- Room Title Area -->
                    <div class="w-40 pr-4 flex flex-col justify-center leading-tight">
                      <span class="text-xs font-bold text-on-surface truncate">${room.name}</span>
                      <span class="text-[10px] text-on-surface-variant font-medium mt-0.5 flex items-center gap-0.5">
                        <span class="material-symbols-outlined text-[12px]">group</span> ${room.capacity} pessoas
                      </span>
                    </div>

                    <!-- Room Track Timeline Area -->
                    <div class="flex-1 h-12 bg-surface rounded-xl relative border border-outline-variant overflow-hidden">
                      
                      <!-- Render Dynamic Bookings inside the timeline track -->
                      ${roomBookings.map(b => {
                        const { left, width } = getTimeOffsets(b.startTime, b.endTime);
                        return `
                          <div class="absolute top-1 bottom-1 left-[${left}%] w-[${width}%] bg-error-container border border-error-base/10 rounded-lg flex items-center px-3 shadow-md border-l-4 border-l-error-base hover:brightness-95 active:scale-[0.99] transition-all cursor-pointer group/item"
                               title="${b.title} (${b.startTime} - ${b.endTime})"
                               hx-get="/api/modals/view-booking?id=${b.id}"
                               hx-target="#modal-container"
                               hx-swap="innerHTML">
                            <span class="text-[10px] font-bold text-on-error-container truncate select-none">${b.title}</span>
                          </div>
                        `;
                      }).join("")}

                      <!-- Empty click target indicator if space is available -->
                      ${roomBookings.length === 0 ? `
                        <div class="absolute inset-0 flex items-center justify-center cursor-pointer bg-secondary-container/5 hover:bg-secondary-container/15 transition-all text-secondary-base"
                             hx-get="/api/modals/create-booking?roomId=${room.id}"
                             hx-target="#modal-container"
                             hx-swap="innerHTML">
                          <span class="text-[10px] font-bold opacity-0 group-hover:opacity-100 transition-opacity">Disponível • Reservar Agora</span>
                        </div>
                      ` : ""}

                    </div>
                  </div>
                `;
              }).join("")}
            </div>

            <!-- Vertical Timeline Indicator Line (Calculated approximate position for mockup time overlay) -->
            <div class="absolute top-0 bottom-0 left-[35%] w-[1.5px] bg-primary-base pointer-events-none z-10 flex flex-col items-center">
              <div class="w-2.5 h-2.5 rounded-full bg-primary-base -mt-1 shadow-md shadow-primary-base"></div>
              <span class="text-[8px] font-bold bg-primary-base text-white px-1.5 py-0.5 rounded-full absolute -bottom-4 shadow-sm select-none">11:30</span>
            </div>

          </div>
        </div>

      </div>

    </div>
  `;
}

function renderRooms(): string {
  updateRoomsDynamicState();
  return `
    <div class="flex flex-col gap-8 max-w-[1400px] mx-auto select-none" id="rooms-view-container">
      
      <!-- Screen Header with CTA buttons -->
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-outline-variant pb-6">
        <div>
          <h2 class="text-2xl mt-2 md:text-3xl font-extrabold text-on-surface tracking-tight">Salas & Instalações</h2>
          <p class="text-sm text-on-surface-variant font-medium mt-1">Gerencie salas de reunião físicas, inventários, capacidades de assento e status de empréstimo.</p>
        </div>
        <div class="flex gap-3 w-full sm:w-auto">
          <button class="flex-1 sm:flex-none border border-outline-border hover:bg-outline-variant/35 text-on-surface text-xs font-semibold py-2.5 px-4 rounded-xl flex items-center justify-center gap-1.5 transition-all cursor-pointer bg-surface-card"
                  hx-get="/api/modals/create-equipment"
                  hx-target="#modal-container"
                  hx-swap="innerHTML">
            <span class="material-symbols-outlined text-[18px]">add</span>
            Cadastrar Equipamento
          </button>
          <button class="flex-1 sm:flex-none bg-primary-base hover:bg-primary-light text-white text-xs font-semibold py-2.5 px-4 rounded-xl flex items-center justify-center gap-1.5 transition-all cursor-pointer shadow-sm shadow-primary-base/10"
                  hx-get="/api/modals/create-room"
                  hx-target="#modal-container"
                  hx-swap="innerHTML">
            <span class="material-symbols-outlined text-[18px]">add</span>
            Cadastrar Sala
          </button>
        </div>
      </div>

      <!-- Page core layout with grid details -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        <!-- Left Side: Rooms Catalog -->
        <div class="lg:col-span-8 flex flex-col gap-4" id="rooms-list-container">
          <h3 class="text-sm font-bold text-on-surface mb-2 tracking-tight">Salas Disponíveis</h3>
          
          ${rooms.map(room => {
            const isAvailable = room.status === "available";
            return `
              <div class="bento-card hover:translate-y-0 hover:shadow-md py-4 px-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 select-none group">
                <div class="flex items-center gap-4 w-full sm:w-auto">
                  
                  <!-- Room Image Thumbnail -->
                  <div class="w-16 h-16 rounded-xl bg-outline-variant/30 overflow-hidden flex-shrink-0 border border-outline-variant shadow-sm relative">
                    <img class="w-full h-full object-cover" src="${room.image}" alt="${room.name}" />
                  </div>

                  <!-- Room Data Details -->
                  <div class="flex-1 sm:flex-initial">
                    <h4 class="font-bold text-sm text-on-surface flex items-center flex-wrap gap-2 leading-none">
                      ${room.name}
                      <span class="inline-block px-2.5 py-0.5 rounded-full text-[9px] font-extrabold uppercase tracking-wide
                                   ${isAvailable ? "bg-[#e6f4ea] text-[#137333]" : "bg-error-container text-on-error-container"}">
                        ${isAvailable ? "Disponível" : "Ocupada"}
                      </span>
                    </h4>
                    <p class="text-xs text-on-surface-variant font-medium flex items-center gap-0.5 mt-1.5">
                      <span class="material-symbols-outlined text-[15px]">group</span> Capacidade: ${room.capacity} pessoas Max
                    </p>
                    
                    <!-- Predefined equipment chips mapping -->
                    <div class="flex gap-1.5 mt-2.5">
                      ${room.equipment.map(eqSymbol => {
                        let nameLabel = eqSymbol === "videocam" ? "Câmera / Projetor" : eqSymbol === "edit_note" ? "Quadro de Vidro" : eqSymbol === "local_cafe" ? "Máquina de Café" : "Display Smart TV";
                        return `
                          <div class="w-7 h-7 rounded-lg bg-surface border border-outline-variant flex items-center justify-center text-on-surface-variant hover:text-primary-base transition-colors" title="${nameLabel}">
                            <span class="material-symbols-outlined text-[15px]">${eqSymbol}</span>
                          </div>
                        `;
                      }).join("")}
                    </div>
                  </div>

                </div>

                <!-- Card actions triggers -->
                <div class="flex gap-1 sm:gap-2 self-end sm:self-auto pt-3 border-t sm:border-none border-outline-variant w-full sm:w-auto justify-end">
                  <button class="p-2 text-outline-border hover:text-primary-base hover:bg-primary-container/20 rounded-lg transition-colors cursor-pointer"
                          hx-get="/api/modals/create-room?editId=${room.id}"
                          hx-target="#modal-container"
                          hx-swap="innerHTML">
                    <span class="material-symbols-outlined text-[18px]">edit</span>
                  </button>
                  <button class="p-2 text-outline-border hover:text-error-base hover:bg-error-container rounded-lg transition-colors cursor-pointer"
                          hx-delete="/api/rooms/${room.id}"
                          hx-target="#rooms-list-container"
                          hx-swap="outerHTML">
                    <span class="material-symbols-outlined text-[18px]">delete</span>
                  </button>
                </div>

              </div>
            `;
          }).join("")}

        </div>

        <!-- Right Side: Mini Inventory Overview -->
        <div class="lg:col-span-4 flex flex-col gap-4">
          <h3 class="text-sm font-bold text-on-surface mb-2 tracking-tight">Inventário de Equipamentos</h3>
          
          <div class="bento-card p-5" id="equipment-list-container">
            <ul class="flex flex-col divide-y divide-outline-variant">
              ${equipments.map(eq => {
                return `
                  <li class="py-3.5 first:pt-0 flex justify-between items-center group/item transition-colors">
                    <div class="flex items-center gap-3">
                      <div class="w-9 h-9 rounded-xl bg-outline-variant/30 flex items-center justify-center text-primary-base shadow-sm">
                        <span class="material-symbols-outlined text-[18px]">${eq.icon}</span>
                      </div>
                      <div>
                        <p class="text-xs font-bold text-on-surface">${eq.name}</p>
                        <p class="text-[10px] font-semibold text-on-surface-variant mt-0.5">Estoque: ${eq.qty} unidades</p>
                      </div>
                    </div>
                    <button class="p-1.5 text-outline-border hover:text-primary-base bg-surface hover:bg-outline-variant/30 border border-outline-variant rounded-lg transition-opacity flex items-center justify-center cursor-pointer md:opacity-0 md:group-hover/item:opacity-100"
                            hx-get="/api/modals/create-equipment?editId=${eq.id}"
                            hx-target="#modal-container"
                            hx-swap="innerHTML">
                      <span class="material-symbols-outlined text-[15px]">edit</span>
                    </button>
                  </li>
                `;
              }).join("")}
            </ul>
          </div>

        </div>

      </div>

    </div>
  `;
}

function renderBookings(): string {
  updateRoomsDynamicState();
  return `
    <div class="flex flex-col gap-8 max-w-[1400px] mx-auto select-none" id="bookings-view-container">
      
      <!-- Sub-Header details -->
      <div class="flex justify-between items-end border-b border-outline-variant pb-6">
        <div>
          <h2 class="text-2xl mt-2 md:text-3xl font-extrabold text-on-surface tracking-tight">Minhas Reservas</h2>
          <p class="text-sm text-on-surface-variant font-medium mt-1">Veja seu histórico de reservas, reuniões agendadas, convites ativos e faça edições rápidas.</p>
        </div>
        <button class="bg-primary-base hover:bg-primary-light text-white text-sm font-semibold px-5 py-2.5 rounded-xl flex items-center gap-1.5 active:scale-[0.98] transition-all cursor-pointer shadow-sm shadow-primary-base/10"
                hx-get="/api/modals/create-booking"
                hx-target="#modal-container"
                hx-swap="innerHTML">
          <span class="material-symbols-outlined text-[18px]">add</span>
          Nova Reserva
        </button>
      </div>

      <!-- Scrollable custom list view of reservations -->
      <div class="bento-card p-0 overflow-hidden border border-outline-variant">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-surface border-b border-outline-variant select-none">
                <th class="px-6 py-4 text-[10px] font-extrabold text-on-surface-variant uppercase tracking-wider">Título da Reunião</th>
                <th class="px-6 py-4 text-[10px] font-extrabold text-on-surface-variant uppercase tracking-wider">Data</th>
                <th class="px-6 py-4 text-[10px] font-extrabold text-on-surface-variant uppercase tracking-wider">Horário</th>
                <th class="px-6 py-4 text-[10px] font-extrabold text-on-surface-variant uppercase tracking-wider">Sala</th>
                <th class="px-6 py-4 text-[10px] font-extrabold text-on-surface-variant uppercase tracking-wider text-center">Ações</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline-variant z-10">
              ${bookings.map(b => {
                const targetRoom = rooms.find(r => r.id === b.room);
                return `
                  <tr class="hover:bg-outline-variant/10 transition-colors">
                    <td class="px-6 py-4">
                      <p class="text-xs font-bold text-on-surface">${b.title}</p>
                    </td>
                    <td class="px-6 py-4 text-xs font-semibold text-on-surface-variant">${b.date}</td>
                    <td class="px-6 py-4 text-xs font-semibold text-on-surface-variant">${b.startTime} - ${b.endTime}</td>
                    <td class="px-6 py-4 select-none">
                      <span class="inline-flex items-center gap-1 px-3 py-1 bg-primary-container text-on-primary-container text-[10px] font-bold rounded-lg uppercase tracking-wider">
                        ${targetRoom ? targetRoom.name : b.room}
                      </span>
                    </td>
                    <td class="px-6 py-4 flex justify-center items-center gap-2 select-none">
                      <button class="p-1.5 text-outline-border hover:bg-error-container hover:text-error-base rounded-md transition-colors cursor-pointer"
                              title="Cancelar Reserva"
                              hx-delete="/api/bookings/${b.id}"
                              hx-target="#main-content"
                              hx-swap="innerHTML">
                        <span class="material-symbols-outlined text-[18px]">delete</span>
                      </button>
                    </td>
                  </tr>
                `;
              }).join("")}

              ${bookings.length === 0 ? `
                <tr>
                  <td colspan="5" class="py-12 text-center text-xs text-on-surface-variant font-medium select-none">
                    <span class="material-symbols-outlined text-4xl text-outline-variant block mb-2">calendar_today</span>
                    Nenhuma reserva agendada para hoje. Escolha uma sala para começar!
                  </td>
                </tr>
              ` : ""}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  `;
}

function renderEquipment(): string {
  return `
    <div class="flex flex-col gap-8 max-w-[1400px] mx-auto select-none" id="equipment-view-panel">
      <!-- Screen Header with CTA buttons -->
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-outline-variant pb-6">
        <div>
          <h2 class="text-2xl mt-2 md:text-3xl font-extrabold text-on-surface tracking-tight">Equipamentos e Serviços</h2>
          <p class="text-sm text-on-surface-variant font-medium mt-1">Gerencie equipamentos multimídia, projetores, displays LCD portáteis, sistemas de áudio e telecomunicação de escritórios.</p>
        </div>
        <button class="bg-primary-base hover:bg-primary-light text-white text-xs font-semibold py-2.5 px-4 rounded-xl flex items-center justify-center gap-1.5 transition-all cursor-pointer shadow-sm shadow-primary-base/10 shadow-md"
                hx-get="/api/modals/create-equipment"
                hx-target="#modal-container"
                hx-swap="innerHTML">
          <span class="material-symbols-outlined text-[18px]">add</span>
          Novo Item
        </button>
      </div>

      <!-- Equipment inventories grid list -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        ${equipments.map(eq => {
          return `
            <div class="bento-card hover:translate-y-0 group hover:shadow-md h-40 flex flex-col justify-between select-none">
              <div class="flex justify-between items-start">
                <div class="w-10 h-10 rounded-xl bg-outline-variant/30 flex items-center justify-center text-primary-base shadow-sm">
                  <span class="material-symbols-outlined text-[20px]">${eq.icon}</span>
                </div>
                
                <div class="flex gap-1.5">
                  <button class="p-1.5 text-outline-border hover:text-primary-base hover:bg-outline-variant/30 border border-outline-variant rounded-lg transition-colors cursor-pointer"
                          hx-get="/api/modals/create-equipment?editId=${eq.id}"
                          hx-target="#modal-container"
                          hx-swap="innerHTML">
                    <span class="material-symbols-outlined text-[15px]">edit</span>
                  </button>
                  <button class="p-1.5 text-outline-border hover:text-error-base hover:bg-error-container border border-outline-variant rounded-lg transition-colors cursor-pointer"
                          hx-delete="/api/equipment/${eq.id}"
                          hx-target="#main-content"
                          hx-swap="innerHTML">
                    <span class="material-symbols-outlined text-[15px]">delete</span>
                  </button>
                </div>
              </div>
              
              <div>
                <h4 class="text-sm font-bold text-on-surface">${eq.name}</h4>
                <div class="flex justify-between items-center mt-2">
                  <span class="text-xs text-on-surface-variant font-medium">Quantidade instalada</span>
                  <span class="text-lg font-extrabold text-primary-base">${eq.qty} unid.</span>
                </div>
              </div>
            </div>
          `;
        }).join("")}
      </div>
    </div>
  `;
}

function renderReports(): string {
  const totalBookings = bookings.length;
  // Calculate average hours
  const peakTime = "10:00 AM - 12:00 PM";
  const utilizationRatio = totalBookings > 0 ? "82%" : "0%";

  return `
    <div class="flex flex-col gap-8 max-w-[1400px] mx-auto select-none" id="reports-view-panel">
      <!-- Screen Header with CTA buttons -->
      <div class="border-b border-outline-variant pb-6 mb-2">
        <h2 class="text-2xl mt-2 md:text-3xl font-extrabold text-on-surface tracking-tight">Painel de Analíticos & Relatórios</h2>
        <p class="text-sm text-on-surface-variant font-medium mt-1">Monitore volumes de agendamento de espaços, picos de ocupação diária e eficiência de capacidade estrutural.</p>
      </div>

      <!-- Telemetry bento card grids -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        <!-- Total schedules gauge -->
        <div class="bento-card py-6 flex flex-col justify-between items-center h-64 text-center">
          <p class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider text-left w-full">Reservas Efetuadas (Hoje)</p>
          
          <!-- Circular SVG metric gauge -->
          <div class="relative flex items-center justify-center w-32 h-32 my-2 select-none">
            <svg class="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="40" stroke="#f1f5f9" stroke-width="8" fill="transparent" />
              <!-- active gauge colored stroke -->
              <circle cx="50" cy="50" r="40" stroke="#3525cd" stroke-width="8" fill="transparent"
                      stroke-dasharray="251.2" stroke-dashoffset="${251.2 - (251.2 * 0.75)}" stroke-linecap="round" />
            </svg>
            <div class="absolute flex flex-col items-center">
              <span class="text-2xl font-extrabold text-on-surface">${totalBookings}</span>
              <span class="text-[9px] font-bold text-on-surface-variant uppercase mt-0.5">Ativas</span>
            </div>
          </div>
          
          <p class="text-[11px] text-on-surface-variant font-medium">Capacidade operacional estável de rede</p>
        </div>

        <!-- Room occupancy efficiency -->
        <div class="bento-card py-6 flex flex-col justify-between h-64">
          <p class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Eficiência de Uso Comum</p>
          
          <div class="space-y-4 my-2 flex-grow flex flex-col justify-center">
            <div>
              <div class="flex justify-between text-xs font-bold text-on-surface mb-1">
                <span>Boardroom Alpha</span>
                <span>85%</span>
              </div>
              <div class="w-full bg-[#f1f5f9] h-2 rounded-full overflow-hidden">
                <div class="bg-primary-base h-full rounded-full" style="width: 85%"></div>
              </div>
            </div>
            
            <div>
              <div class="flex justify-between text-xs font-bold text-on-surface mb-1">
                <span>Huddle Room 1</span>
                <span>60%</span>
              </div>
              <div class="w-full bg-[#f1f5f9] h-2 rounded-full overflow-hidden">
                <div class="bg-primary-light h-full rounded-full" style="width: 60%"></div>
              </div>
            </div>
            
            <div>
              <div class="flex justify-between text-xs font-bold text-on-surface mb-1">
                <span>Studio B</span>
                <span>35%</span>
              </div>
              <div class="w-full bg-[#f1f5f9] h-2 rounded-full overflow-hidden">
                <div class="bg-secondary-container h-full rounded-full" style="width: 35%"></div>
              </div>
            </div>
          </div>
          
          <p class="text-[11px] text-on-surface-variant font-medium">Médias ponderadas por tempo de locação ativa</p>
        </div>

        <!-- Hours usage highlights -->
        <div class="bento-card py-6 flex flex-col justify-between h-64">
          <p class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Picos de Lotação Presencial</p>
          
          <div class="flex flex-col justify-center flex-grow py-3">
            <span class="text-3xl font-extrabold text-primary-base tracking-tight select-all">${peakTime}</span>
            <p class="text-[11px] text-[#137333] font-bold mt-2.5 flex items-center gap-1 bg-[#e6f4ea] px-3 py-1.5 rounded-lg w-fit">
              <span class="material-symbols-outlined text-[15px] symbol-filled">done_all</span>
              Utilização média consolidada: ${utilizationRatio}
            </p>
          </div>

          <p class="text-[11px] text-on-surface-variant font-medium">Taxas calculadas a partir de dados históricos Semanais</p>
        </div>

      </div>

    </div>
  `;
}

// -------------------------------------------------------------
// Interactive Modal UI Generators
// -------------------------------------------------------------
function renderCreateBookingModal(preSelectedRoomId?: string): string {
  const tomorrow = "2026-05-31"; // prefilled mockup coordinates
  
  return `
    <div id="modal-overlay" class="fixed inset-0 bg-on-surface/40 backdrop-blur-sm z-50 flex items-center justify-center p-4 modal-backdrop">
      
      <!-- Modal Inner Card (Bento Design Element) -->
      <div id="modal-container-elem" class="bg-white w-full max-w-2xl rounded-2xl shadow-[0px_10px_35px_rgba(0,0,0,0.12)] border border-outline-variant flex flex-col modal-animate overflow-hidden max-h-[90vh]">
        
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-5 border-b border-outline-variant bg-surface select-none">
          <div>
            <h2 class="text-lg font-bold text-on-surface tracking-tight">Criar Nova Reserva</h2>
            <p class="text-xs text-on-surface-variant font-medium mt-0.5">Agende espaços de reunião e recursos multimídia.</p>
          </div>
          <button class="text-on-surface-variant hover:text-primary-base transition-colors hover:bg-outline-variant/30 p-2 rounded-xl flex items-center justify-center cursor-pointer"
                  onclick="window.closeModal()">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <!-- Form and Core input body -->
        <div class="p-6 overflow-y-auto flex-1 h-full select-none">
          <form id="booking-form" 
                hx-post="/api/bookings" 
                hx-target="#main-content" 
                hx-swap="innerHTML"
                class="flex flex-col gap-6">
            
            <!-- Meeting title parameter -->
            <div class="flex flex-col gap-1.5">
              <label for="meeting-title" class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Título da Reunião</label>
              <input type="text" id="meeting-title" name="title" required
                     placeholder="Ex: Sync de Alinhamento de Produto, Q3 Review, etc."
                     class="w-full bg-white border border-outline-variant rounded-xl px-4 py-2.5 text-xs text-on-surface focus:outline-none focus:border-primary-base focus:ring-1 focus:ring-primary-base transition-colors placeholder:text-on-surface-variant/40" />
            </div>

            <!-- Date and Hours layout parameter -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              
              <!-- Date configuration -->
              <div class="flex flex-col gap-1.5">
                <label for="booking-date" class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Data de Agendamento</label>
                <div class="relative">
                  <span class="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-outline-border text-[16px] pointer-events-none">calendar_today</span>
                  <input type="date" id="booking-date" name="date" required value="${tomorrow}"
                         class="w-full bg-white border border-outline-variant rounded-xl pl-11 pr-4 py-2.5 text-xs text-on-surface focus:outline-none focus:border-primary-base focus:ring-1 focus:ring-primary-base transition-colors pointer-events-auto cursor-pointer" />
                </div>
              </div>

              <!-- Sub hours dropdown parameters -->
              <div class="grid grid-cols-2 gap-2">
                <div class="flex flex-col gap-1.5">
                  <label for="start-time" class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Início</label>
                  <select id="start-time" name="startTime" required
                          class="w-full bg-white border border-outline-variant rounded-xl px-3 py-2.5 text-xs text-on-surface focus:outline-none focus:border-primary-base focus:ring-1 focus:ring-primary-base transition-colors cursor-pointer appearance-none">
                    <option value="09:00 AM">09:00 AM</option>
                    <option value="10:00 AM" selected>10:00 AM</option>
                    <option value="11:00 AM">11:00 AM</option>
                    <option value="12:00 PM">12:00 PM</option>
                    <option value="01:00 PM">01:00 PM</option>
                    <option value="02:00 PM">02:00 PM</option>
                    <option value="03:00 PM">03:00 PM</option>
                  </select>
                </div>
                
                <div class="flex flex-col gap-1.5">
                  <label for="end-time" class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Fim</label>
                  <select id="end-time" name="endTime" required
                          class="w-full bg-white border border-outline-variant rounded-xl px-3 py-2.5 text-xs text-on-surface focus:outline-none focus:border-primary-base focus:ring-1 focus:ring-primary-base transition-colors cursor-pointer appearance-none">
                    <option value="10:00 AM">10:00 AM</option>
                    <option value="11:00 AM" selected>11:00 AM</option>
                    <option value="12:00 PM">12:00 PM</option>
                    <option value="01:00 PM">01:00 PM</option>
                    <option value="02:00 PM">02:00 PM</option>
                    <option value="03:00 PM">03:00 PM</option>
                    <option value="04:00 PM">04:00 PM</option>
                  </select>
                </div>
              </div>

            </div>

            <!-- Visual Space selecting selector -->
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Selecione o Espaço de Reunião</label>
              
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-1">
                ${rooms.map(room => {
                  const isChecked = preSelectedRoomId ? preSelectedRoomId === room.id : room.id === "boardroom-a";
                  return `
                    <div data-room-card="${room.id}"
                         onclick="window.selectRoomInModal('${room.id}')"
                         class="group relative bg-white rounded-xl p-4 cursor-pointer transition-all border 
                                ${isChecked ? "border-2 border-primary-base shadow-sm" : "border-outline-variant"}">
                      
                      <!-- Radio Sync tracker (hidden visually but checked on selectRoomInModal trigger) -->
                      <input type="radio" name="roomId" value="${room.id}" ${isChecked ? "checked" : ""} class="sr-only" />

                      <div class="absolute top-3 right-3 check-badge-container flex items-center justify-center text-primary-base bg-white rounded-full"
                           style="${isChecked ? "display: flex;" : "display: none;"}">
                        <span class="material-symbols-outlined text-[18px] symbol-filled">check_circle</span>
                      </div>

                      <div class="w-8 h-8 rounded-full flex items-center justify-center text-on-surface-variant sm:mb-2.5 room-icon-container
                                  ${isChecked ? "bg-primary-container/20 text-primary-base" : "bg-outline-variant/30"}">
                        <span class="material-symbols-outlined text-[16px]">meeting_room</span>
                      </div>

                      <h4 class="font-extrabold text-[12px] text-on-surface truncate leading-tight">${room.name}</h4>
                      <p class="text-[10px] text-on-surface-variant font-medium mt-0.5">${room.capacity} pessoas</p>
                    </div>
                  `;
                }).join("")}
              </div>
            </div>

            <!-- Equipment chips checklist parameter options -->
            <div class="flex flex-col gap-2">
              <label class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Equipamentos Solicitados (Opcional)</label>
              <div class="flex flex-wrap gap-2 mt-1">
                ${equipments.map(eq => {
                  return `
                    <div onclick="window.toggleEquipmentInModal(this)"
                         class="flex items-center gap-2 px-3 py-2 rounded-full border border-outline-variant bg-surface-lowest text-on-surface-variant transition-all hover:border-primary-base/50 cursor-pointer select-none">
                      <input type="checkbox" name="equipment" value="${eq.id}" class="sr-only" />
                      <span class="material-symbols-outlined text-[16px]">${eq.icon}</span>
                      <span class="text-[11px] font-bold">${eq.name}</span>
                    </div>
                  `;
                }).join("")}
              </div>
            </div>

          </form>
        </div>

        <!-- Footer actions CTA -->
        <div class="px-6 py-4 border-t border-outline-variant bg-surface flex justify-end gap-3 select-none">
          <button class="px-5 py-2 rounded-xl border border-outline-border bg-white text-on-surface text-xs font-semibold hover:bg-outline-variant/30 cursor-pointer transition-colors"
                  onclick="window.closeModal()">
            Cancelar
          </button>
          <button form="booking-form" type="submit"
                  class="px-5 py-2 rounded-xl bg-primary-base hover:bg-primary-light active:scale-[0.98] text-white text-xs font-semibold shadow-sm transition-all cursor-pointer">
            Confirmar Reserva
          </button>
        </div>

      </div>
    </div>
  `;
}

function renderCreateRoomModal(editRoomId?: string): string {
  const targetRoom = editRoomId ? rooms.find(r => r.id === editRoomId) : null;
  return `
    <div id="modal-overlay" class="fixed inset-0 bg-on-surface/40 backdrop-blur-sm z-50 flex items-center justify-center p-4 modal-backdrop">
      <div id="modal-container-elem" class="bg-white w-full max-w-md rounded-2xl shadow-[0px_10px_35px_rgba(0,0,0,0.12)] border border-outline-variant flex flex-col modal-animate overflow-hidden">
        
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 bg-surface border-b border-outline-variant select-none">
          <h2 class="text-sm font-bold text-on-surface tracking-tight">${targetRoom ? "Editar Sala" : "Cadastrar Nova Sala"}</h2>
          <button class="text-on-surface-variant hover:text-primary-base transition-colors hover:bg-outline-variant/30 p-1.5 rounded-lg flex items-center justify-center cursor-pointer"
                  onclick="window.closeModal()">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <!-- Form and Input blocks -->
        <div class="p-6">
          <form id="room-form" 
                hx-post="/api/rooms" 
                hx-target="#main-content" 
                hx-swap="innerHTML"
                class="flex flex-col gap-4">
            
            ${targetRoom ? `<input type="hidden" name="editId" value="${targetRoom.id}" />` : ""}

            <div class="flex flex-col gap-1.5">
              <label for="room-name" class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Nome da Sala</label>
              <input type="text" id="room-name" name="name" required value="${targetRoom ? targetRoom.name : ""}"
                     placeholder="Ex: Sala Gama, Auditório Central"
                     class="w-full bg-white border border-outline-variant rounded-xl px-4 py-2 text-xs text-on-surface focus:outline-none focus:border-primary-base focus:ring-1 focus:ring-primary-base" />
            </div>

            <div class="flex flex-col gap-1.5">
              <label for="room-capacity" class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Capacidade Máxima (Pessoas)</label>
              <input type="number" id="room-capacity" name="capacity" required value="${targetRoom ? targetRoom.capacity : "6"}"
                     class="w-full bg-white border border-outline-variant rounded-xl px-4 py-2 text-xs text-on-surface focus:outline-none focus:border-primary-base focus:ring-1 focus:ring-primary-base" />
            </div>

            <div class="flex flex-col gap-1.5">
              <label for="room-image" class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">URL da Imagem da Sala (Placeholder)</label>
              <input type="url" id="room-image" name="image" value="${targetRoom ? targetRoom.image : "https://lh3.googleusercontent.com/aida-public/AB6AXuAWojhQV4tHPXBwK2Eg-vjB0Kgq3iT7Sv5TmsIq92P7QXLLh772nRonO1yPvd042F2r0xx2hGSu1gxLGvRjPvs0WosoJ8mQteK3vvV40SBSK9vSYI7qfrl-OMg8TPGQDPXI-ZEoK7yKIKMpDnlml2bRsKy5pGnZ2D6GY3kWs3S-UgCGY6BN_LFRG2pBjd_4NXc4w0Nlpw89Kd-O867KHRZmT_PWabbBrBT-nZ2d1H7nrfsPpB6Ab8MPql2OsIkDaESc-kdH7SSi9HUc"}"
                     class="w-full bg-white border border-outline-variant rounded-xl px-4 py-2 text-xs text-on-surface focus:outline-none focus:border-primary-base focus:ring-1 focus:ring-primary-base" />
            </div>

            <!-- Equips checkboxes -->
            <div class="flex flex-col gap-1.5 mt-1 select-none">
              <label class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Comodidades Pré-instaladas</label>
              <div class="flex flex-col gap-2 mt-1">
                <label class="flex items-center gap-2 text-xs font-semibold cursor-pointer">
                  <input type="checkbox" name="equipment" value="videocam" 
                         ${targetRoom && targetRoom.equipment.includes("videocam") ? "checked" : !targetRoom ? "checked" : ""}
                         class="rounded border-outline-variant text-primary-base focus:ring-primary-base" />
                  <span>Projetor Multimídia / Câmera de Conferência</span>
                </label>
                <label class="flex items-center gap-2 text-xs font-semibold cursor-pointer">
                  <input type="checkbox" name="equipment" value="edit_note" 
                         ${targetRoom && targetRoom.equipment.includes("edit_note") ? "checked" : !targetRoom ? "checked" : ""}
                         class="rounded border-outline-variant text-primary-base focus:ring-primary-base" />
                  <span>Quadro de Vidro / Painel para Esboços</span>
                </label>
                <label class="flex items-center gap-2 text-xs font-semibold cursor-pointer">
                  <input type="checkbox" name="equipment" value="local_cafe" 
                         ${targetRoom && targetRoom.equipment.includes("local_cafe") ? "checked" : ""}
                         class="rounded border-outline-variant text-primary-base focus:ring-primary-base" />
                  <span>Estação de Café Expresso Gratuito</span>
                </label>
                <label class="flex items-center gap-2 text-xs font-semibold cursor-pointer">
                  <input type="checkbox" name="equipment" value="tv" 
                         ${targetRoom && targetRoom.equipment.includes("tv") ? "checked" : ""}
                         class="rounded border-outline-variant text-primary-base focus:ring-primary-base" />
                  <span>Painel Smart TV 65" Interativo</span>
                </label>
              </div>
            </div>

          </form>
        </div>

        <!-- Footer Actions buttons -->
        <div class="px-6 py-4 border-t border-outline-variant bg-surface flex justify-end gap-3 select-none">
          <button class="px-4 py-2 rounded-xl border border-outline-border bg-white text-on-surface text-xs font-bold hover:bg-outline-variant/30 cursor-pointer"
                  onclick="window.closeModal()">
            Cancelar
          </button>
          <button form="room-form" type="submit"
                  class="px-4 py-2 rounded-xl bg-primary-base hover:bg-primary-light text-white text-xs font-bold shadow-sm cursor-pointer">
            Confirmar
          </button>
        </div>

      </div>
    </div>
  `;
}

function renderCreateEquipmentModal(editEqId?: string): string {
  const targetEq = editEqId ? equipments.find(e => e.id === editEqId) : null;
  return `
    <div id="modal-overlay" class="fixed inset-0 bg-on-surface/40 backdrop-blur-sm z-50 flex items-center justify-center p-4 modal-backdrop">
      <div id="modal-container-elem" class="bg-white w-full max-w-sm rounded-2xl shadow-[0px_10px_35px_rgba(0,0,0,0.12)] border border-outline-variant flex flex-col modal-animate overflow-hidden">
        
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 bg-surface border-b border-outline-variant select-none">
          <h2 class="text-sm font-bold text-on-surface tracking-tight">${targetEq ? "Editar Equipamento" : "Cadastrar Equipamento"}</h2>
          <button class="text-on-surface-variant hover:text-primary-base transition-colors hover:bg-outline-variant/30 p-1.5 rounded-lg flex items-center justify-center cursor-pointer"
                  onclick="window.closeModal()">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <!-- Form fields body -->
        <div class="p-6">
          <form id="eq-form" 
                hx-post="/api/equipment" 
                hx-target="#main-content" 
                hx-swap="innerHTML"
                class="flex flex-col gap-4">
            
            ${targetEq ? `<input type="hidden" name="editId" value="${targetEq.id}" />` : ""}

            <div class="flex flex-col gap-1.5">
              <label for="eq-name" class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Nome do Item</label>
              <input type="text" id="eq-name" name="name" required value="${targetEq ? targetEq.name : ""}"
                     placeholder="Ex: Teclado Mecânico, Cabos HDMI"
                     class="w-full bg-white border border-outline-variant rounded-xl px-4 py-2 text-xs text-on-surface focus:outline-none focus:border-primary-base" />
            </div>

            <div class="flex flex-col gap-1.5">
              <label for="eq-qty" class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Quantidade em Estoque</label>
              <input type="number" id="eq-qty" name="qty" required value="${targetEq ? targetEq.qty : "1"}"
                     class="w-full bg-white border border-outline-variant rounded-xl px-4 py-2 text-xs text-on-surface focus:outline-none focus:border-primary-base" />
            </div>

            <div class="flex flex-col gap-1.5">
              <label for="eq-icon" class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Ícone de Símbolo (Material Name)</label>
              <select id="eq-icon" name="icon" class="w-full bg-white border border-outline-variant rounded-xl px-3 py-2 text-xs text-on-surface">
                <option value="videocam" ${targetEq && targetEq.icon === "videocam" ? "selected" : ""}>Projetor / Vídeo</option>
                <option value="tv" ${targetEq && targetEq.icon === "tv" ? "selected" : ""}>Painel Smart TV / LCD</option>
                <option value="edit_note" ${targetEq && targetEq.icon === "edit_note" ? "selected" : ""}>Caderno / Notas</option>
                <option value="local_cafe" ${targetEq && targetEq.icon === "local_cafe" ? "selected" : ""}>Alimentação / Café</option>
                <option value="home_repair_service" ${targetEq && targetEq.icon === "home_repair_service" ? "selected" : ""}>Serviços Gerais</option>
              </select>
            </div>

          </form>
        </div>

        <!-- Actions -->
        <div class="px-6 py-4 border-t border-outline-variant bg-surface flex justify-end gap-3 select-none">
          <button class="px-4 py-2 rounded-xl border border-outline-border bg-white text-on-surface text-xs font-bold hover:bg-outline-variant/30 cursor-pointer"
                  onclick="window.closeModal()">
            Cancelar
          </button>
          <button form="eq-form" type="submit"
                  class="px-4 py-2 rounded-xl bg-primary-base hover:bg-primary-light text-white text-xs font-bold shadow-sm cursor-pointer">
            Confirmar
          </button>
        </div>

      </div>
    </div>
  `;
}

function renderBookingViewModal(bookId: string): string {
  const b = bookings.find(x => x.id === bookId);
  if (!b) return `<script>window.closeModal();</script>`;
  const targetRoom = rooms.find(r => r.id === b.room);

  return `
    <div id="modal-overlay" class="fixed inset-0 bg-on-surface/40 backdrop-blur-sm z-50 flex items-center justify-center p-4 modal-backdrop">
      <div id="modal-container-elem" class="bg-white w-full max-w-sm rounded-2xl shadow-[0px_10px_35px_rgba(0,0,0,0.12)] border border-outline-variant flex flex-col modal-animate overflow-hidden">
        
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 bg-surface border-b border-outline-variant select-none">
          <h2 class="text-xs font-bold text-on-surface tracking-tight">Detalhes do Agendamento</h2>
          <button class="text-on-surface-variant hover:text-primary-base transition-colors hover:bg-outline-variant/30 p-1.5 rounded-lg flex items-center justify-center cursor-pointer"
                  onclick="window.closeModal()">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <div class="p-6 flex flex-col gap-4 select-none text-left">
          <div>
            <span class="text-[10px] font-extrabold text-primary-base uppercase bg-primary-container/40 px-2 py-0.5 rounded-md">${targetRoom ? targetRoom.name : b.room}</span>
            <h3 class="text-base font-extrabold text-on-surface mt-2 leading-tight">${b.title}</h3>
          </div>

          <div class="grid grid-cols-2 gap-4 border-t border-b border-outline-variant py-4">
            <div>
              <p class="text-[10px] text-on-surface-variant font-bold uppercase tracking-wide">Data</p>
              <p class="text-xs font-bold text-on-surface mt-0.5">${b.date}</p>
            </div>
            <div>
              <p class="text-[10px] text-on-surface-variant font-bold uppercase tracking-wide">Horário</p>
              <p class="text-xs font-bold text-on-surface mt-0.5">${b.startTime} - ${b.endTime}</p>
            </div>
          </div>

          ${b.equipment && b.equipment.length > 0 ? `
            <div>
              <p class="text-[10px] text-on-surface-variant font-bold uppercase tracking-wide">Equipamentos Solicitados</p>
              <div class="flex flex-wrap gap-1 mt-1.5">
                ${b.equipment.map(eqId => {
                  const item = equipments.find(x => x.id === eqId) || { name: eqId };
                  return `<span class="px-2 py-1 bg-[#f1f5f9] text-on-surface text-[10px] font-bold rounded-full">${item.name}</span>`;
                }).join("")}
              </div>
            </div>
          ` : ""}
        </div>

        <!-- Footer trigger cancellation directly -->
        <div class="px-6 py-4 border-t border-outline-variant bg-surface flex justify-between select-none">
          <button class="px-4 py-2 rounded-xl bg-error-container text-on-error-container text-xs font-bold hover:brightness-95 active:scale-[0.98] transition-all cursor-pointer flex items-center gap-1"
                  hx-delete="/api/bookings/${b.id}"
                  hx-target="#main-content"
                  hx-swap="innerHTML">
            <span class="material-symbols-outlined text-[15px]">delete</span>
            Excluir Reserva
          </button>
          <button class="px-4 py-2 rounded-xl border border-outline-border bg-white text-on-surface text-xs font-bold hover:bg-outline-variant/30 cursor-pointer"
                  onclick="window.closeModal()">
            Fechar
          </button>
        </div>

      </div>
    </div>
  `;
}

// -------------------------------------------------------------
// Server Initialization with Express Web Entry Layer
// -------------------------------------------------------------
async function bootstrapServer() {
  const app = express();
  const PORT = 3000;

  // URL-encode parse for standard HTMX submits payloads
  app.use(express.urlencoded({ extended: true }));
  app.use(express.json());

  // 1. Dynamic Routing Endpoints serving View HTML segments
  // -------------------------------------------------------------
  app.get("/api/views/dashboard", (req, res) => {
    res.send(renderDashboard());
  });

  app.get("/api/views/rooms", (req, res) => {
    res.send(renderRooms());
  });

  app.get("/api/views/bookings", (req, res) => {
    res.send(renderBookings());
  });

  app.get("/api/views/equipment", (req, res) => {
    res.send(renderEquipment());
  });

  app.get("/api/views/reports", (req, res) => {
    res.send(renderReports());
  });

  // 2. Modals View Engines routing
  // -------------------------------------------------------------
  app.get("/api/modals/create-booking", (req, res) => {
    const roomId = req.query.roomId as string | undefined;
    res.send(renderCreateBookingModal(roomId));
  });

  app.get("/api/modals/create-room", (req, res) => {
    const editId = req.query.editId as string | undefined;
    res.send(renderCreateRoomModal(editId));
  });

  app.get("/api/modals/create-equipment", (req, res) => {
    const editId = req.query.editId as string | undefined;
    res.send(renderCreateEquipmentModal(editId));
  });

  app.get("/api/modals/view-booking", (req, res) => {
    const id = req.query.id as string || "";
    res.send(renderBookingViewModal(id));
  });

  // 3. Form action APIs (CRUD records operations)
  // -------------------------------------------------------------
  
  // Create / Register Booking
  app.post("/api/bookings", (req, res) => {
    const { title, date, startTime, endTime, roomId, equipment } = req.body;
    
    // Create new booking record
    const eqArray = Array.isArray(equipment) ? equipment : equipment ? [equipment] : [];
    const newBooking: Booking = {
      id: "book-" + Date.now(),
      title: title || "Reunião de Alinhamento",
      date: date || "2026-05-31",
      startTime: startTime || "10:00 AM",
      endTime: endTime || "11:00 AM",
      room: roomId || "boardroom-a",
      equipment: eqArray
    };

    bookings.unshift(newBooking); // add to top of lists
    
    // Automatically close the modal on successful HTMX load + render dashboard as active swap view
    res.send(renderDashboard() + `<script>window.closeModal();</script>`);
  });

  // Cancel Booking
  app.delete("/api/bookings/:id", (req, res) => {
    const { id } = req.params;
    bookings = bookings.filter(b => b.id !== id);
    
    // Return tables update alongside modal auto wipeout scripts
    res.send(renderBookings() + `<script>window.closeModal();</script>`);
  });

  // Create / Edit Rooms
  app.post("/api/rooms", (req, res) => {
    const { editId, name, capacity, image, equipment } = req.body;
    const eqArray = Array.isArray(equipment) ? equipment : equipment ? [equipment] : [];

    if (editId) {
      // Edit
      const room = rooms.find(r => r.id === editId);
      if (room) {
        room.name = name;
        room.capacity = parseInt(capacity, 10) || room.capacity;
        room.image = image || room.image;
        room.equipment = eqArray;
      }
    } else {
      // Create
      const newRoom: Room = {
        id: "room-" + Date.now(),
        name: name || "Nova Sala de Negócios",
        capacity: parseInt(capacity, 10) || 6,
        status: "available",
        image: image || "https://lh3.googleusercontent.com/aida-public/AB6AXuAWojhQV4tHPXBwK2Eg-vjB0Kgq3iT7Sv5TmsIq92P7QXLLh772nRonO1yPvd042F2r0xx2hGSu1gxLGvRjPvs0WosoJ8mQteK3vvV40SBSK9vSYI7qfrl-OMg8TPGQDPXI-ZEoK7yKIKMpDnlml2bRsKy5pGnZ2D6GY3kWs3S-UgCGY6BN_LFRG2pBjd_4NXc4w0Nlpw89Kd-O867KHRZmT_PWabbBrBT-nZ2d1H7nrfsPpB6Ab8MPql2OsIkDaESc-kdH7SSi9HUc",
        equipment: eqArray
      };
      rooms.push(newRoom);
    }

    res.send(renderRooms() + `<script>window.closeModal();</script>`);
  });

  // Delete Room
  app.delete("/api/rooms/:id", (req, res) => {
    const { id } = req.params;
    rooms = rooms.filter(r => r.id !== id);
    bookings = bookings.filter(b => b.room !== id); // clear dependent bookings
    
    // Return fresh updated catalog
    res.send(renderRooms());
  });

  // Create / Edit Equipment Material assets
  app.post("/api/equipment", (req, res) => {
    const { editId, name, qty, icon } = req.body;
    
    if (editId) {
      const eq = equipments.find(e => e.id === editId);
      if (eq) {
        eq.name = name;
        eq.qty = parseInt(qty, 10) || eq.qty;
        eq.icon = icon || eq.icon;
      }
    } else {
      const newEq: Equipment = {
        id: "eq-" + Date.now(),
        name: name || "Novo Recurso",
        qty: parseInt(qty, 10) || 1,
        icon: icon || "home_repair_service"
      };
      equipments.push(newEq);
    }

    res.send(renderRooms() + `<script>window.closeModal();</script>`);
  });

  // Delete Equipment
  app.delete("/api/equipment/:id", (req, res) => {
    const { id } = req.params;
    equipments = equipments.filter(e => e.id !== id);
    res.send(renderEquipment());
  });

  // 4. Vite middleware for dev or standard compiled files serve fallback in prod
  // -------------------------------------------------------------
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa"
    });
    app.use(vite.middlewares);
  } else {
    // Serve production static assets compiled under dist folder
    const distPath = pathNode.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(pathNode.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`[Workspace Portal] Servidor Express rodando na URL: http://localhost:${PORT}`);
  });
}

bootstrapServer();
