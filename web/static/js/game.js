document.addEventListener('DOMContentLoaded', () => {
    // 1. Initial State Initialization from embedded gameData
    const game = window.gameData;
    if (!game) return;

    let activeRow = null;
    let activeCol = null;
    let pencilMode = false;
    let startTime = new Date(game.started_at);
    let timerInterval = null;
    let heartbeatInterval = null;
    let currentElapsedSeconds = game.accumulated_seconds;

    // References to DOM elements
    const gridTable = document.getElementById('sudoku-grid');
    const timerDisplay = document.getElementById('timer-display');
    const hintsLabel = document.getElementById('hints-counter-label');
    const togglePencil = document.getElementById('pencil-mode-checkbox');
    const btnErase = document.getElementById('btn-erase-cell');
    const btnHint = document.getElementById('btn-get-hint');
    const keypad = document.getElementById('numeric-keypad');

    // 2. Initialize Game Grid values
    const initialBoard = game.initial_board;
    const currentBoard = game.current_board;
    const solution = game.solution;

    function initBoardUI() {
        for (let r = 0; r < 9; r++) {
            for (let c = 0; c < 9; c++) {
                const cell = document.getElementById(`cell-${r}-${c}`);
                const valueContainer = cell.querySelector('.cell-value');
                const val = currentBoard[r][c];
                const isGiven = (initialBoard[r][c] !== 0);

                if (isGiven) {
                    cell.classList.add('given-cell');
                    valueContainer.textContent = val;
                } else if (val !== 0) {
                    cell.classList.add('player-cell');
                    valueContainer.textContent = val;

                    // If error highlighting is on, check correctness on startup (only for Beginner and Easy)
                    const showErrors = (game.difficulty === 'BEGINNER' || game.difficulty === 'EASY');
                    if (game.settings.highlight_errors && showErrors && val !== solution[r][c]) {
                        cell.classList.add('error-cell');
                    }
                }
            }
        }
        updateKeypadAssist();
    }

    // Beginner mode helper: Checks if a value would create a rule violation (duplicate)
    function isInvalidValue(row, col, val) {
        if (val === 0) return false;
        
        // Check row
        for (let c = 0; c < 9; c++) {
            if (c !== col && currentBoard[row][c] === val) return true;
        }
        // Check col
        for (let r = 0; r < 9; r++) {
            if (r !== row && currentBoard[r][col] === val) return true;
        }
        // Check 3x3 box
        const boxStartRow = Math.floor(row / 3) * 3;
        const boxStartCol = Math.floor(col / 3) * 3;
        for (let r = boxStartRow; r < boxStartRow + 3; r++) {
            for (let c = boxStartCol; c < boxStartCol + 3; c++) {
                if (!(r === row && c === col) && currentBoard[r][c] === val) return true;
            }
        }
        return false;
    }

    // Greys out or disables keypad buttons for numbers that lead to invalid attempts (Beginner Mode only)
    function updateKeypadAssist() {
        if (!keypad) return;
        const isBeginner = (game.difficulty === 'BEGINNER');
        
        for (let val = 1; val <= 9; val++) {
            const btn = keypad.querySelector(`[data-key="${val}"]`);
            if (!btn) continue;
            
            if (isBeginner && activeRow !== null && activeCol !== null) {
                if (isInvalidValue(activeRow, activeCol, val)) {
                    btn.classList.add('disabled-key');
                    btn.disabled = true;
                } else {
                    btn.classList.remove('disabled-key');
                    btn.disabled = false;
                }
            } else {
                btn.classList.remove('disabled-key');
                btn.disabled = false;
            }
        }
    }

    // 3. Highlight Cell row/col/box intersections
    function selectCell(row, col) {
        // Clear all previous highlight classes
        const cells = gridTable.querySelectorAll('.sudoku-cell');
        cells.forEach(c => {
            c.classList.remove('selected-cell', 'related-cell', 'same-value-cell');
        });

        activeRow = row;
        activeCol = col;

        const activeCell = document.getElementById(`cell-${row}-${col}`);
        activeCell.classList.add('selected-cell');

        const activeVal = activeCell.querySelector('.cell-value').textContent;

        const boxStartRow = Math.floor(row / 3) * 3;
        const boxStartCol = Math.floor(col / 3) * 3;

        // Apply highlights based on user settings
        for (let r = 0; r < 9; r++) {
            for (let c = 0; c < 9; c++) {
                const cell = document.getElementById(`cell-${r}-${c}`);
                const cellVal = cell.querySelector('.cell-value').textContent;

                // Under highlight_related setting
                if (game.settings.highlight_related) {
                    const inRow = (r === row);
                    const inCol = (c === col);
                    const inBox = (r >= boxStartRow && r < boxStartRow + 3 && c >= boxStartCol && c < boxStartCol + 3);

                    if ((inRow || inCol || inBox) && !(r === row && c === col)) {
                        cell.classList.add('related-cell');
                    }
                }

                // If cell has the same non-empty value, highlight it
                if (activeVal !== '' && cellVal === activeVal && !(r === row && c === col)) {
                    cell.classList.add('same-value-cell');
                }
            }
        }
        updateKeypadAssist();
    }

    // 4. Handle grid click events
    gridTable.addEventListener('click', (e) => {
        const cell = e.target.closest('.sudoku-cell');
        if (!cell) return;

        const row = parseInt(cell.getAttribute('data-row'), 10);
        const col = parseInt(cell.getAttribute('data-col'), 10);
        selectCell(row, col);
    });

    // 5. Input Handler: Place moves or toggle pencil notes
    async function handleCellInput(value) {
        if (activeRow === null || activeCol === null) return;
        
        // Cannot edit given starting cells
        if (initialBoard[activeRow][activeCol] !== 0) return;

        const cell = document.getElementById(`cell-${activeRow}-${activeCol}`);
        const valSpan = cell.querySelector('.cell-value');
        const pencilNotesGrid = cell.querySelector('.pencil-notes-grid');

        // Handle erasure
        if (value === 0) {
            currentBoard[activeRow][activeCol] = 0; // Sync client state board
            valSpan.textContent = '';
            cell.classList.remove('player-cell', 'error-cell', 'hint-cell');
            pencilNotesGrid.querySelectorAll('.pencil-note').forEach(n => n.textContent = '');
            
            // Sync with backend API
            try {
                await fetch('/game/api/move', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ row: activeRow, col: activeCol, value: 0 })
                });
            } catch (err) {
                console.error("Failed to sync erase:", err);
            }
            
            // Re-highlight the same value cells
            selectCell(activeRow, activeCol);
            return;
        }

        // Handle pencil notes mode
        if (pencilMode) {
            currentBoard[activeRow][activeCol] = 0; // Erase cell value if we use pencil notes
            valSpan.textContent = '';
            cell.classList.remove('player-cell', 'error-cell', 'hint-cell');
            
            const noteSpan = pencilNotesGrid.querySelector(`[data-note-val="${value}"]`);
            if (noteSpan.textContent === '') {
                noteSpan.textContent = value;
            } else {
                noteSpan.textContent = '';
            }
            updateKeypadAssist();
            return;
        }

        // Beginner mode keypad/keyboard assist: Prevent invalid duplicates from placement entirely
        if (game.difficulty === 'BEGINNER') {
            if (isInvalidValue(activeRow, activeCol, value)) {
                // Obvious duplicate conflicts -> block entry, flash red shake animation
                cell.classList.add('invalid-flash');
                setTimeout(() => cell.classList.remove('invalid-flash'), 500);
                return;
            }
        }

        // Clear notes if placing normal cell value
        pencilNotesGrid.querySelectorAll('.pencil-note').forEach(n => n.textContent = '');

        // POST move to backend server API
        try {
            const response = await fetch('/game/api/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ row: activeRow, col: activeCol, value: value })
            });

            if (!response.ok) return;
            const data = await response.json();

            if (data.invalid) {
                // Obvious duplicate conflicts -> block entry, flash red shake animation
                cell.classList.add('invalid-flash');
                setTimeout(() => cell.classList.remove('invalid-flash'), 500);
                return;
            }

            if (data.won) {
                // Stop heartbeats and timer immediately
                clearInterval(timerInterval);
                clearInterval(heartbeatInterval);

                // Game solved! Display solved value, trigger redirect after success
                valSpan.textContent = value;
                cell.classList.remove('error-cell');
                cell.classList.add('player-cell');
                
                // Redirect directly to victory page with stat query parameters
                window.location.href = `/victory/${data.game_id}?rating_before=${data.rating_before}&rating_after=${data.rating_after}&rank_before=${data.rank_before || ''}&rank_after=${data.rank_after || ''}`;
                return;
            }

            if (data.correct) {
                currentBoard[activeRow][activeCol] = value; // Sync client state board
                valSpan.textContent = value;
                cell.classList.add('player-cell');

                // Error highlight settings (only for Beginner and Easy)
                const showErrors = (game.difficulty === 'BEGINNER' || game.difficulty === 'EASY');
                if (game.settings.highlight_errors && showErrors) {
                    if (data.solution_match === false) {
                        cell.classList.add('error-cell');
                    } else {
                        cell.classList.remove('error-cell');
                    }
                } else {
                    cell.classList.remove('error-cell');
                }
                
                // Re-highlight select to update "same-value-cell" indicators
                selectCell(activeRow, activeCol);
            }
        } catch (err) {
            console.error("Failed to post move:", err);
        }
    }

    // 6. Utility: Reveal Hint API trigger
    async function revealHint() {
        try {
            const response = await fetch('/game/api/hint', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) return;
            const data = await response.json();

            const cell = document.getElementById(`cell-${data.row}-${data.col}`);
            const valSpan = cell.querySelector('.cell-value');
            const pencilNotesGrid = cell.querySelector('.pencil-notes-grid');

            currentBoard[data.row][data.col] = data.value; // Sync client board state
            pencilNotesGrid.querySelectorAll('.pencil-note').forEach(n => n.textContent = '');
            valSpan.textContent = data.value;
            cell.classList.remove('error-cell');
            cell.classList.add('player-cell', 'hint-cell');

            hintsLabel.textContent = `Hints: ${data.hints_used}`;

            if (data.won) {
                clearInterval(timerInterval);
                clearInterval(heartbeatInterval);
                window.location.href = `/victory/${data.game_id}?rating_before=${data.rating_before}&rating_after=${data.rating_after}&rank_before=${data.rank_before || ''}&rank_after=${data.rank_after || ''}`;
            } else {
                selectCell(data.row, data.col);
            }
        } catch (err) {
            console.error("Failed to get hint:", err);
        }
    }

    // 7. Navigation: Handle arrow key navigation and numeric entry
    document.addEventListener('keydown', (e) => {
        if (activeRow === null || activeCol === null) return;

        // Allow arrow keys to navigate the board
        if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectCell(Math.max(0, activeRow - 1), activeCol);
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectCell(Math.min(8, activeRow + 1), activeCol);
        } else if (e.key === 'ArrowLeft') {
            e.preventDefault();
            selectCell(activeRow, Math.max(0, activeCol - 1));
        } else if (e.key === 'ArrowRight') {
            e.preventDefault();
            selectCell(activeRow, Math.min(8, activeCol + 1));
        }
        
        // 1-9 to place/pencil values
        else if (e.key >= '1' && e.key <= '9') {
            handleCellInput(parseInt(e.key, 10));
        }
        
        // Backspace or Delete or 0 to erase
        else if (e.key === 'Backspace' || e.key === 'Delete' || e.key === '0') {
            e.preventDefault();
            handleCellInput(0);
        }
    });

    // 8. Keypad & Actions Event Bindings
    if (keypad) {
        keypad.addEventListener('click', (e) => {
            const btn = e.target.closest('.keypad-btn');
            if (!btn) return;
            const val = parseInt(btn.getAttribute('data-key'), 10);
            handleCellInput(val);
        });
    }

    if (btnErase) {
        btnErase.addEventListener('click', () => handleCellInput(0));
    }

    if (btnHint) {
        btnHint.addEventListener('click', revealHint);
    }

    if (togglePencil) {
        togglePencil.addEventListener('change', (e) => {
            pencilMode = e.target.checked;
        });
    }

    // 9. Real-time timer update loop
    if (timerDisplay) {
        function updateTimer() {
            const now = new Date();
            const elapsedSeconds = Math.floor((now - startTime) / 1000) + game.accumulated_seconds;
            currentElapsedSeconds = elapsedSeconds;
            
            const hrs = Math.floor(elapsedSeconds / 3600);
            const mins = Math.floor((elapsedSeconds % 3600) / 60);
            const secs = elapsedSeconds % 60;

            const format = (num) => String(num).padStart(2, '0');

            if (hrs > 0) {
                timerDisplay.textContent = `${format(hrs)}:${format(mins)}:${format(secs)}`;
            } else {
                timerDisplay.textContent = `${format(mins)}:${format(secs)}`;
            }
        }

        updateTimer();
        timerInterval = setInterval(updateTimer, 1000);
    }

    // 10. Background Heartbeat & Exit Clock Pausing
    function sendHeartbeat(isBeacon = false) {
        const payload = JSON.stringify({ elapsed_seconds: currentElapsedSeconds });
        if (isBeacon) {
            try {
                // keepalive: true ensures the browser completes the request even on page exit/close
                fetch('/game/api/heartbeat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: payload,
                    keepalive: true
                });
            } catch (err) {
                console.error("Keepalive heartbeat failed:", err);
            }
        } else {
            fetch('/game/api/heartbeat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: payload
            }).catch(err => {
                console.error("Background heartbeat failed:", err);
            });
        }
    }

    // Interval every 5 seconds
    heartbeatInterval = setInterval(() => sendHeartbeat(false), 5000);

    // Save final elapsed seconds on tab close, hide, or navigation
    window.addEventListener('pagehide', () => sendHeartbeat(true));
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
            sendHeartbeat(true);
        }
    });

    // Clear interval bindings on resign button click
    const resignForm = document.getElementById('resign-form');
    if (resignForm) {
        resignForm.addEventListener('submit', () => {
            clearInterval(timerInterval);
            clearInterval(heartbeatInterval);
            sendHeartbeat(true); // Sync one last time before POST
        });
    }

    // Initialize board on load
    initBoardUI();
});

