// ===== CONSTANTS & CONFIG =====
const LABEL_WIDTH_MM = 100;
const LABEL_HEIGHT_MM = 60;
const DPU = 3.78; // Dots per unit (mm to pixel approx at 96dpi)
const CANVAS_W = 378; // 100mm * 3.78
const CANVAS_H = 227; // 60mm * 3.78

// ===== ZONE COLORS =====
const ZONE_COLORS = {
  A: { bg: '#3b82f6', name: 'Azul',     nameEn: 'Blue',   nameZh: '蓝色' },
  B: { bg: '#22c55e', name: 'Verde',    nameEn: 'Green',  nameZh: '绿色' },
  C: { bg: '#f59e0b', name: 'Amarillo', nameEn: 'Yellow', nameZh: '黄色' },
  D: { bg: '#ef4444', name: 'Rojo',     nameEn: 'Red',    nameZh: '红色' },
  E: { bg: '#8b5cf6', name: 'Púrpura',  nameEn: 'Purple', nameZh: '紫色' },
  F: { bg: '#06b6d4', name: 'Cian',     nameEn: 'Cyan',   nameZh: '青色' },
  G: { bg: '#f97316', name: 'Naranja',  nameEn: 'Orange', nameZh: '橙色' },
  H: { bg: '#ec4899', name: 'Rosa',     nameEn: 'Pink',   nameZh: '粉色' },
};

// ===== i18n =====
let currentLang = 'es';
const i18n = {
  es: {
    pageTitle: 'GENERADOR DE ETIQUETAS DE UBICACIÓN',
    pageSubtitle: 'Formato 100 × 60 mm · Code128 + QR',
    livePreview: 'Vista previa en tiempo real',
    singleLabel: 'Etiqueta Individual',
    zone: 'Zona', aisle: 'Pasillo', rack: 'Estantería', shelf: 'Nivel',
    companyName: 'Nombre empresa',
    btnAdd: 'Agregar Etiqueta',
    batchGen: 'Generación por Lotes',
    batchZone: 'Zona', batchAisles: 'Pasillos', batchRacks: 'Estanterías', batchShelves: 'Niveles',
    batchUnit: 'etiquetas a generar',
    btnBatch: 'Generar Lote',
    btnPDF: 'Guardar PDF',
    btnClear: 'Limpiar',
    colorLegend: 'Leyenda de Colores',
    preview: 'Vista Previa',
    gridView: 'Cuadrícula',
    emptyTitle: 'Sin etiquetas',
    emptyMsg: 'Configura la ubicación en el panel izquierdo y presiona "Agregar"',
    labelUnit: 'etiquetas',
    descZone: 'Zona', descAisle: 'Pasillo', descRack: 'Estantería', descShelf: 'Nivel',
    toastAdded: 'Etiqueta agregada',
    toastBatch: 'etiquetas generadas',
    toastCleared: 'Etiquetas eliminadas',
    toastGeneratingPDF: 'Generando PDF...',
    toastPDFReady: 'PDF descargado',
    toastImageReady: 'Imagen descargada',
    generatingPDF: 'Generando PDF',
    btnDownloadImage: 'Descargar Imagen',
    cancel: 'Cancelar',
    processStarted: 'Iniciando generación...',
  },
  en: {
    pageTitle: 'LOCATION LABEL GENERATOR',
    pageSubtitle: '100 × 60 mm format · Code128 + QR',
    livePreview: 'Real-time preview',
    singleLabel: 'Single Label',
    zone: 'Zone', aisle: 'Aisle', rack: 'Rack', shelf: 'Shelf',
    companyName: 'Company name',
    btnAdd: 'Add Label',
    batchGen: 'Batch Generation',
    batchZone: 'Zone', batchAisles: 'Aisles', batchRacks: 'Racks', batchShelves: 'Shelves',
    batchUnit: 'labels to generate',
    btnBatch: 'Generate Batch',
    btnPDF: 'Save PDF',
    btnClear: 'Clear',
    colorLegend: 'Color Legend',
    preview: 'Preview',
    gridView: 'Grid view',
    emptyTitle: 'No labels',
    emptyMsg: 'Set location on the left panel and press "Add"',
    labelUnit: 'labels',
    descZone: 'Zone', descAisle: 'Aisle', descRack: 'Rack', descShelf: 'Shelf',
    toastAdded: 'Label added',
    toastBatch: 'labels generated',
    toastCleared: 'Labels cleared',
    toastGeneratingPDF: 'Generating PDF...',
    toastPDFReady: 'PDF downloaded',
    toastImageReady: 'Image downloaded',
    generatingPDF: 'Generating PDF',
    btnDownloadImage: 'Download Image',
    cancel: 'Cancel',
    processStarted: 'Starting generation...',
  },
  zh: {
    pageTitle: '仓库位置标签生成器',
    pageSubtitle: '100 × 60 mm 格式 · Code128 + QR',
    livePreview: '实时预览',
    singleLabel: '单个标签',
    zone: '区域', aisle: '通道', rack: '货架', shelf: '层',
    companyName: '公司名称',
    btnAdd: '添加标签',
    batchGen: '批量生成',
    batchZone: '区域', batchAisles: '通道', batchRacks: '货架', batchShelves: '层',
    batchUnit: '个标签待生成',
    btnBatch: '批量生成',
    btnPDF: '保存 PDF',
    btnClear: '清除',
    colorLegend: '颜色图例',
    preview: '预览',
    gridView: '网格视图',
    emptyTitle: '暂无标签',
    emptyMsg: '在左侧面板设置位置信息后点击"添加"',
    labelUnit: '个标签',
    descZone: '区', descAisle: '道', descRack: '架', descShelf: '层',
    toastAdded: '标签已添加',
    toastBatch: '个标签已生成',
    toastCleared: '标签已清除',
    toastGeneratingPDF: '正在生成 PDF...',
    toastPDFReady: 'PDF 已下载',
    toastImageReady: '图片已下载',
    generatingPDF: '正在生成 PDF',
    btnDownloadImage: '下载图片',
    cancel: '取消',
    processStarted: '开始生成...',
  }
};

async function setLanguage(lang) {
  currentLang = lang;
  for (const b of document.querySelectorAll('.lang-btn')) {
    const active = b.dataset.lang === lang;
    b.classList.toggle('active', active);
    b.style.background = active ? 'rgba(34,211,238,0.15)' : '';
    b.style.color = active ? '#22d3ee' : '';
  }
  for (const el of document.querySelectorAll('[data-i18n]')) {
    const key = el.dataset.i18n;
    if (i18n[lang]?.[key]) el.textContent = i18n[lang][key];
  }

  // Re-render preview and all labels in area
  updateLivePreview();
  const area = document.getElementById('printArea');
  const cards = area.querySelectorAll('.label-card');
  for (const card of cards) {
    const canvas = card.querySelector('canvas');
    if (canvas) {
      await drawLabelToCanvas(canvas, {
        zone: card.dataset.zone,
        aisle: card.dataset.aisle,
        rack: card.dataset.rack,
        shelf: card.dataset.shelf,
        company: card.dataset.company
      });
    }
  }

  buildLegend();
  updateBatchCount();
  updateCounter();
}

// ===== ZONE DOT =====
function updateZoneDot() {
  const z = document.getElementById('inpZone').value;
  const c = ZONE_COLORS[z]?.bg || '#666';
  const dot = document.getElementById('zoneDot');
  if (dot) {
    dot.style.background = c;
    dot.style.color = c;
  }
}
function updateBatchZoneDot() {
  const z = document.getElementById('batchZone').value;
  const c = ZONE_COLORS[z]?.bg || '#666';
  const dot = document.getElementById('batchZoneDot');
  if (dot) {
    dot.style.background = c;
    dot.style.color = c;
  }
}

// ===== LEGEND =====
function buildLegend() {
  const grid = document.getElementById('legendGrid');
  if (!grid) return;
  grid.innerHTML = '';
  for (const [letter, z] of Object.entries(ZONE_COLORS)) {
    const colorName = currentLang === 'en' ? z.nameEn : currentLang === 'zh' ? z.nameZh : z.name;
    grid.innerHTML += `<div class="flex items-center gap-1.5 px-1.5 py-1 rounded-md bg-surface-700/60 cursor-default" title="${colorName}">
      <div class="w-3 h-3 rounded-sm shrink-0" style="background:${z.bg}; box-shadow:0 0 4px ${z.bg}40"></div>
      <span class="text-[9px] text-content-muted font-mono font-bold">${letter}</span>
    </div>`;
  }
}

// ===== BATCH COUNT =====
function updateBatchCount() {
  const a = parseInt(document.getElementById('batchAisles').value) || 0;
  const r = parseInt(document.getElementById('batchRacks').value) || 0;
  const s = parseInt(document.getElementById('batchShelves').value) || 0;
  const countEl = document.getElementById('batchCount');
  if (countEl) countEl.textContent = a * r * s;
}

// ===== LABEL COUNTER =====
function updateCounter() {
  const count = document.querySelectorAll('#printArea .label-card').length;
  const counterEl = document.getElementById('labelCounter');
  if (counterEl) counterEl.textContent = count;
  const emptyState = document.getElementById('emptyState');
  if (emptyState) emptyState.style.display = count > 0 ? 'none' : 'flex';
}

// ===== TOAST =====
function showToast(msg, color) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.style.background = color || '#22c55e';
  el.classList.add('show');
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.remove('show'), 2000);
}

// ===== GRID TOGGLE =====
function toggleGrid() {
  const area = document.getElementById('printArea');
  if (!area) return;
  const showGridEl = document.getElementById('showGrid');
  const checked = showGridEl ? showGridEl.checked : true;
  area.style.gap = checked ? '16px' : '8px';
}

// ===== CORE CANVAS RENDERER =====
async function drawLabelToCanvas(canvas, data) {
  const ctx = canvas.getContext('2d');
  const { zone, aisle, rack, shelf, company } = data;
  const color = ZONE_COLORS[zone]?.bg || '#666';
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
  const startY = 15; // Balanced top margin

  // 3. Main Code Text
  ctx.fillStyle = '#0f172a';
  ctx.font = '800 32px "JetBrains Mono", monospace';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'top';
  ctx.fillText(code, startX, startY);

  // 4. Multi-language Badges
  const rows = [
    { labels: i18n.es },
    { labels: i18n.zh },
    { labels: i18n.en }
  ];

  let currentBadgeY = startY + 48; // More space below code
  const badgeH = 17;
  const badgeSpacing = 3;

  ctx.font = '700 9px Inter, sans-serif';

  for (const row of rows) {
    let badgeX = startX;
    const labels = row.labels;
    const badgeTexts = [
      `${labels.zone} ${zone}`,
      `${labels.aisle} ${pad2(aisle)}`,
      `${labels.rack} ${pad2(rack)}`,
      `${labels.shelf} ${pad2(shelf)}`
    ];

    for (const text of badgeTexts) {
      const textToDraw = text.toUpperCase();
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
    currentBadgeY += badgeH + badgeSpacing;
  }

  // 5. Barcode (Code128)
  const barcodeCanvas = document.createElement('canvas');
  const sharedBottomY = 210; // Lowered baseline
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
  } catch (e) { console.error('Barcode error:', e); }

  ctx.fillStyle = '#475569';
  ctx.font = '500 8.5px "JetBrains Mono", monospace';
  ctx.textAlign = 'left';
  ctx.fillText(code, startX + 90, sharedBottomY + 4);

  // 6. QR Code
  const qrDim = 32;
  const qrX = CANVAS_W - qrDim - 12;
  const qrY = sharedBottomY - qrDim - 4;

  const qrTempCanvas = document.createElement('canvas');
  await window.QRCode.toCanvas(qrTempCanvas, code, { margin: 0, width: qrDim });
  ctx.drawImage(qrTempCanvas, qrX, qrY, qrDim, qrDim);

  // 7. Company Name
  ctx.fillStyle = '#94a3b8';
  ctx.font = '600 7px Inter, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  ctx.letterSpacing = '1.5px';
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

// ===== HELPERS =====
function pad2(n) { return String(n).padStart(2, '0'); }

function getInputs() {
  const zoneEl = document.getElementById('inpZone');
  const aisleEl = document.getElementById('inpAisle');
  const rackEl = document.getElementById('inpRack');
  const shelfEl = document.getElementById('inpShelf');
  const companyEl = document.getElementById('inpCompany');

  return {
    zone: zoneEl ? zoneEl.value : 'A',
    aisle: aisleEl ? (parseInt(aisleEl.value) || 1) : 1,
    rack: rackEl ? (parseInt(rackEl.value) || 1) : 1,
    shelf: shelfEl ? (parseInt(shelfEl.value) || 1) : 1,
    company: (companyEl && companyEl.value) ? companyEl.value : 'SYNETECH',
    lang: currentLang
  };
}

// ===== LIVE PREVIEW =====
async function updateLivePreview() {
  const container = document.getElementById('livePreviewContainer');
  if (!container) return;

  let canvas = container.querySelector('canvas');
  if (!canvas) {
    canvas = document.createElement('canvas');
    canvas.className = 'w-full h-full object-contain';
    container.innerHTML = '';
    container.appendChild(canvas);
  }
  await drawLabelToCanvas(canvas, getInputs());
}

// ===== CREATE FULL-SIZE LABEL =====
async function createLabel(data) {
  const card = document.createElement('div');
  card.className = 'label-card label-animate relative group';
  // Store data for re-renders or exports
  card.dataset.zone = data.zone;
  card.dataset.aisle = data.aisle;
  card.dataset.rack = data.rack;
  card.dataset.shelf = data.shelf;
  card.dataset.company = data.company;

  const canvas = document.createElement('canvas');
  canvas.style.width = '100%';
  canvas.style.height = '100%';
  await drawLabelToCanvas(canvas, data);
  card.appendChild(canvas);

  const delBtn = document.createElement('button');
  delBtn.className = 'label-delete absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity';
  delBtn.innerHTML = '&times;';
  delBtn.onclick = () => { card.remove(); updateCounter(); };
  card.appendChild(delBtn);

  return card;
}

// ===== ADD SINGLE =====
async function addSingleLabel() {
  const data = getInputs();
  const area = document.getElementById('printArea');
  if (!area) return;
  const label = await createLabel(data);
  area.appendChild(label);
  updateCounter();
  showToast(`${i18n[currentLang].toastAdded}: ${data.zone}-${pad2(data.aisle)}-${pad2(data.rack)}-${pad2(data.shelf)}`, '#0891b2');
}

// ===== BATCH =====
async function generateBatch() {
  const zone = document.getElementById('batchZone').value;
  const maxA = parseInt(document.getElementById('batchAisles').value) || 1;
  const maxR = parseInt(document.getElementById('batchRacks').value) || 1;
  const maxS = parseInt(document.getElementById('batchShelves').value) || 1;
  const company = (document.getElementById('inpCompany') && document.getElementById('inpCompany').value) || 'SYNETECH';
  const area = document.getElementById('printArea');
  if (!area) return;

  let count = 0;
  for (let a = 1; a <= maxA; a++) {
    for (let r = 1; r <= maxR; r++) {
      for (let s = 1; s <= maxS; s++) {
        const label = await createLabel({ zone, aisle: a, rack: r, shelf: s, company });
        label.style.animationDelay = `${count * 15}ms`;
        area.appendChild(label);
        count++;
      }
    }
  }
  updateCounter();
  showToast(`${count} ${i18n[currentLang].toastBatch}`, '#7c3aed');
}


// ===== PDF GENERATION (One label per page 100x60mm) =====
async function generatePDF() {
  const { jsPDF } = window.jspdf;
  const area = document.getElementById('printArea');
  const cards = Array.from(area.querySelectorAll('.label-card'));
  if (cards.length === 0) return;

  showToast(i18n[currentLang].toastGeneratingPDF, '#3b82f6');

  const pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: [100, 60] });

  for (let i = 0; i < cards.length; i++) {
    const canvas = cards[i].querySelector('canvas');
    if (i > 0) pdf.addPage([100, 60], 'landscape');
    if (canvas) {
        pdf.addImage(canvas.toDataURL('image/jpeg', 0.95), 'JPEG', 0, 0, 100, 60);
    }
  }
  pdf.save(`etiquetas-${Date.now()}.pdf`);
  showToast(i18n[currentLang].toastPDFReady, '#22c55e');
}

// ===== DOWNLOAD IMAGE (Live Preview) =====
async function downloadLivePreviewImage() {
  const container = document.getElementById('livePreviewContainer');
  const canvas = container ? container.querySelector('canvas') : null;
  if (!canvas) return;

  const data = getInputs();
  const filename = `${data.zone}-${pad2(data.aisle)}-${pad2(data.rack)}-${pad2(data.shelf)}.png`;

  const link = document.createElement('a');
  link.download = filename;
  link.href = canvas.toDataURL('image/png', 1.0);
  link.click();
  showToast(i18n[currentLang].toastImageReady, '#22c55e');
}

// ===== CLEAR =====
function clearLabels() {
  const area = document.getElementById('printArea');
  if (!area) return;
  const cards = area.querySelectorAll('.label-card');
  if (cards.length === 0) return;
  for (const c of cards) {
    c.remove();
  }
  updateCounter();
  showToast(i18n[currentLang].toastCleared, '#64748b');
}

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {
    buildLegend();
    const aislesInput = document.getElementById('batchAisles');
    if (aislesInput) {
        aislesInput.addEventListener('input', updateBatchCount);
    }
    const racksInput = document.getElementById('batchRacks');
    if (racksInput) {
        racksInput.addEventListener('input', updateBatchCount);
    }
    const shelvesInput = document.getElementById('batchShelves');
    if (shelvesInput) {
        shelvesInput.addEventListener('input', updateBatchCount);
    }

    // Theme Toggle Logic
    const themeToggleBtn = document.getElementById('theme-toggle');
    const darkIcon = document.getElementById('theme-toggle-dark-icon');
    const lightIcon = document.getElementById('theme-toggle-light-icon');
    const htmlElement = document.documentElement;

    const updateIcons = (isLight) => {
        if (!darkIcon || !lightIcon) return;
        if (isLight) {
            darkIcon.classList.remove('theme-icon-active');
            darkIcon.classList.add('theme-icon-inactive');
            lightIcon.classList.remove('theme-icon-inactive');
            lightIcon.classList.add('theme-icon-active');
        } else {
            darkIcon.classList.remove('theme-icon-inactive');
            darkIcon.classList.add('theme-icon-active');
            lightIcon.classList.remove('theme-icon-active');
            lightIcon.classList.add('theme-icon-inactive');
        }
    };

    const savedTheme = localStorage.getItem('theme');
    const systemPrefersLight = window.matchMedia('(prefers-color-scheme: light)').matches;
    const isLightInitial = savedTheme === 'light' || (!savedTheme && systemPrefersLight);

    if (isLightInitial) {
        htmlElement.classList.add('light');
        htmlElement.classList.remove('dark');
    } else {
        htmlElement.classList.add('dark');
        htmlElement.classList.remove('light');
    }
    updateIcons(isLightInitial);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const isLight = htmlElement.classList.toggle('light');
            if (isLight) {
                htmlElement.classList.remove('dark');
            } else {
                htmlElement.classList.add('dark');
            }
            updateIcons(isLight);
            localStorage.setItem('theme', isLight ? 'light' : 'dark');
        });
    }

    // Input listeners for preview
    const inputs = ['inpZone', 'inpAisle', 'inpRack', 'inpShelf', 'inpCompany'];
    for (const id of inputs) {
      const el = document.getElementById(id);
      if (el) el.addEventListener('input', () => {
        updateLivePreview();
        if (id === 'inpZone') updateZoneDot();
      });
    }

    // Batch input listeners
    const batchInputs = ['batchZone', 'batchAisles', 'batchRacks', 'batchShelves'];
    for (const id of batchInputs) {
      const el = document.getElementById(id);
      if (el) el.addEventListener('input', () => {
        updateBatchCount();
        if (id === 'batchZone') updateBatchZoneDot();
      });
    }

    // Back Button Logic
    const backBtn = document.querySelector('header button svg path[d="M15 19l-7-7 7-7"]')?.closest('button');
    if (backBtn) {
        backBtn.addEventListener('click', () => history.back());
    }

    const downloadBtn = document.getElementById('btnDownloadPreview');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadLivePreviewImage);
    }

    updateBatchCount();
    updateZoneDot();
    updateBatchZoneDot();
    setLanguage('es').then(() => {
        updateLivePreview();
    });
});
