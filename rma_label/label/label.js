// ===== CONSTANTS & CONFIG =====
const CANVAS_W = 378; // 100mm * 3.78
const CANVAS_H = 227; // 60mm * 3.78

const ZONE_COLORS = {
    A: { bg: '#3b82f6', name: 'Azul' },
    B: { bg: '#22c55e', name: 'Verde' },
    C: { bg: '#f59e0b', name: 'Amarillo' },
    D: { bg: '#ef4444', name: 'Rojo' },
    E: { bg: '#8b5cf6', name: 'Púrpura' },
    F: { bg: '#06b6d4', name: 'Cian' },
    G: { bg: '#f97316', name: 'Naranja' },
    H: { bg: '#ec4899', name: 'Rosa' },
};

// ===== CORE CANVAS RENDERER =====
async function drawLabelToCanvas(canvas, data) {
    const ctx = canvas.getContext('2d');
    const { zone, aisle, rack, shelf, company } = data;
    const color = ZONE_COLORS[zone]?.bg || '#666';
    const pad2 = (n) => String(n).padStart(2, '0');
    const code = `${zone}-${pad2(aisle)}-${pad2(rack)}-${pad2(shelf)}`;

    // Reset & Clear
    canvas.width = CANVAS_W;
    canvas.height = CANVAS_H;
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);

    // 1. Zone Stripe
    ctx.fillStyle = color;
    ctx.fillRect(0, 0, 36, CANVAS_H);

    // Stripe gradient shadow
    const grad = ctx.createLinearGradient(30, 0, 36, 0);
    grad.addColorStop(0, 'rgba(0,0,0,0.08)');
    grad.addColorStop(1, 'transparent');
    ctx.fillStyle = grad;
    ctx.fillRect(30, 0, 6, CANVAS_H);

    // 2. Zone Letter
    ctx.fillStyle = '#ffffff';
    ctx.font = '900 24px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(zone, 18, CANVAS_H / 2);

    // Body Padding/Offset
    const startX = 52;
    const startY = 15;

    // 3. Main Code Text
    ctx.fillStyle = '#0f172a';
    ctx.font = '800 32px "JetBrains Mono", monospace';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText(code, startX, startY);

    // 4. Badges (Simplified for Demo)
    const badgeLabels = [
        { key: 'ZONA', val: zone },
        { key: 'PASILLO', val: pad2(aisle) },
        { key: 'ESTANTE', val: pad2(rack) },
        { key: 'NIVEL', val: pad2(shelf) }
    ];

    let currentBadgeY = startY + 48;
    const badgeH = 17;
    ctx.font = '700 9px Inter, sans-serif';

    let badgeX = startX;
    for (const badge of badgeLabels) {
        const textToDraw = `${badge.key} ${badge.val}`;
        const textWidth = ctx.measureText(textToDraw).width;
        const badgeW = textWidth + 14;

        // Draw Badge Background
        ctx.fillStyle = '#f8fafc';
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 1;
        roundRect(ctx, badgeX, currentBadgeY, badgeW, badgeH, 4, true, true);

        // Draw Badge Text
        ctx.fillStyle = '#334155';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(textToDraw, badgeX + badgeW / 2, currentBadgeY + badgeH / 2 + 0.5);

        badgeX += badgeW + 4;
    }

    // 5. Barcode (Code128)
    const barcodeCanvas = document.createElement('canvas');
    const sharedBottomY = 180;
    const barcodeW = 220;

    try {
        window.JsBarcode(barcodeCanvas, code, {
            format: 'CODE128',
            width: 2,
            height: 50,
            displayValue: false,
            margin: 0
        });
        ctx.drawImage(barcodeCanvas, startX, sharedBottomY - 54, barcodeW, 50);
    } catch (e) {
        console.error('Barcode error:', e);
        ctx.fillStyle = '#ef4444';
        ctx.fillText('Barcode Error', startX, sharedBottomY - 20);
    }

    ctx.fillStyle = '#475569';
    ctx.font = '500 8.5px "JetBrains Mono", monospace';
    ctx.textAlign = 'left';
    ctx.fillText(code, startX + 90, sharedBottomY + 4);

    // 6. QR Code
    const qrDim = 32;
    const qrX = CANVAS_W - qrDim - 12;
    const qrY = sharedBottomY - qrDim - 4;

    try {
        const qrTempCanvas = document.createElement('canvas');
        await window.QRCode.toCanvas(qrTempCanvas, code, { margin: 0, width: qrDim });
        ctx.drawImage(qrTempCanvas, qrX, qrY, qrDim, qrDim);
    } catch (e) {
        console.error('QR Error:', e);
    }

    // 7. Company Name
    ctx.fillStyle = '#94a3b8';
    ctx.font = '600 7px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText(company.toUpperCase(), qrX + qrDim / 2, sharedBottomY);
}

// Helper for rounded rectangles
function roundRect(ctx, x, y, width, height, radius, fill, stroke) {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + width - radius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    ctx.lineTo(x + width, y + height - radius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    ctx.lineTo(x + radius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
    if (fill) ctx.fill();
    if (stroke) ctx.stroke();
}

// ===== INIT =====
window.addEventListener('load', () => {
    const canvas = document.getElementById('labelCanvas');
    const sampleData = {
        zone: 'A',
        aisle: 12,
        rack: 4,
        shelf: 1,
        company: 'SYNETECH'
    };

    // Draw initial label
    drawLabelToCanvas(canvas, sampleData);
});
