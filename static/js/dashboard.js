(function () {
            const TIMELINE_START = 9;   // 09:00
            const TIMELINE_HOURS = 6;   // 09:00 – 15:00

            /** "HH:MM" → decimal hours */
            function toDecimal(timeStr) {
                const [h, m] = timeStr.split(':').map(Number);
                return h + m / 60;
            }

            /** Fraction of track width (0–1) → nearest 15-min "HH:MM" */
            function offsetToTime(fraction) {
                const totalMinutes = Math.round((TIMELINE_START + fraction * TIMELINE_HOURS) * 60 / 15) * 15;
                const h = Math.floor(totalMinutes / 60);
                const m = totalMinutes % 60;
                return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}`;
            }

            /** True if clickedTime falls inside any booking interval */
            function hasConflict(bookings, clickedTime) {
                const t = toDecimal(clickedTime);
                return bookings.some(b => t >= toDecimal(b.start) && t < toDecimal(b.end));
            }

            /** Show a brief toast message */
            function showToast(msg) {
                const toast = document.getElementById('conflict-toast');
                const label = document.getElementById('conflict-toast-msg');
                label.textContent = msg;
                toast.classList.remove('hidden');
                toast.classList.add('flex');
                clearTimeout(toast._timer);
                toast._timer = setTimeout(() => {
                    toast.classList.add('hidden');
                    toast.classList.remove('flex');
                }, 3000);
            }

            document.querySelectorAll('.booking-track').forEach(track => {
                track.addEventListener('click', function (e) {
                    // Click landed on an occupied block → conflict
                    if (e.target.closest('.booking-block')) {
                        showToast('Horário já reservado para esta sala.');
                        return;
                    }

                    const roomId   = this.dataset.roomId;
                    const date     = this.dataset.date;
                    const bookings = JSON.parse(this.dataset.bookings || '[]');

                    // Map click position → time
                    const rect     = this.getBoundingClientRect();
                    const fraction = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
                    const startTime = offsetToTime(fraction);

                    if (hasConflict(bookings, startTime)) {
                        showToast('Horário já reservado para esta sala.');
                        return;
                    }

                    // Suggest a 1-hour window capped at timeline end
                    const startDec = toDecimal(startTime);
                    const endDec   = Math.min(startDec + 1, TIMELINE_START + TIMELINE_HOURS);
                    const endH = Math.floor(endDec);
                    const endM = Math.round((endDec - endH) * 60);
                    const endTime = `${String(endH).padStart(2,'0')}:${String(endM).padStart(2,'0')}`;

                    const params = new URLSearchParams({
                        sala: roomId,
                        data: date,
                        hora_inicio: startTime,
                        hora_fim: endTime,
                    });

                    const targetUrl = `${window.NOVA_RESERVA_URL}?${params.toString()}`;
                    // Prefer modal fetch injection; fallback to full navigation
                    const modalContainer = document.getElementById('modal-container');
                    if (modalContainer && window.fetch) {
                        fetch(targetUrl, {
                            credentials: 'same-origin',
                            headers: {
                                'HX-Request': 'true'
                            }
                        })
                            .then(r => {
                                if (!r.ok) {
                                    console.error('fetch failed:', r.status, r.statusText);
                                    throw new Error('network error: ' + r.status);
                                }
                                return r.text();
                            })
                            .then(html => {
                                if (html) {
                                    modalContainer.innerHTML = html;
                                } else {
                                    console.warn('empty response, navigating to URL');
                                    window.location.href = targetUrl;
                                }
                            })
                            .catch((err) => {
                                console.error('modal fetch error:', err);
                                window.location.href = targetUrl;
                            });
                    } else {
                        window.location.href = targetUrl;
                    }
                });
            });
        })();