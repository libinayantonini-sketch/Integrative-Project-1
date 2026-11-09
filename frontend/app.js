const $ = (s, e = document) => e.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const Cfg = {
  get() {
    let c = {}; try { c = JSON.parse(localStorage.getItem('cfg')) || {}; } catch { c = {}; }
    const cl = Array.isArray(c.classes) ? c.classes.filter(x => typeof x === 'string' && x.trim()).map(x => x.trim()) : [];
    return { porPagina: [5, 10, 25, 50].includes(+c.porPagina) ? +c.porPagina : 10, classes: cl.length ? cl : ['Placa', 'Semáforo'] };
  },
  set(v) { try { localStorage.setItem('cfg', JSON.stringify({ ...Cfg.get(), ...v })); return true; } catch { return false; } }
};
const STATUS = { na_fila: ['Na fila', 'gray'], processando: ['Processando', 'blue'], concluida: ['Concluída', 'green'], falhou: ['Falhou', 'red'] };
const REV = { pendente: ['Pendente', 'gray'], confirmada: ['Confirmada', 'green'], rejeitada: ['Rejeitada', 'red'], corrigida: ['Corrigida', 'blue'] };
const pick = (m, k) => Object.hasOwn(m, k) ? m[k] : null;
const tag = (m, k) => { const [t, c] = pick(m, k) || [k || '—', 'gray']; return `<span class="tag ${c}">${esc(t)}</span>`; };
const mmss = s => { s = Math.round(+s || 0); return String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0'); };
const fdata = d => { const t = new Date(d); return d && !isNaN(t) ? t.toLocaleDateString('pt-BR', { timeZone: 'UTC' }) : '—'; };
const pct = p => Math.round((+p || 0) * 100) + '%';
const safe = async (p, fb) => { try { return { d: await p, e: null }; } catch (e) { return { d: fb, e: e.message }; } };
const aviso = (e, zerados) => e ? `<div class="aviso" role="alert"><b>Falha ao carregar:</b> ${esc(e)}${zerados ? ' Os valores abaixo não foram carregados e aparecem zerados.' : ''}</div>` : '';
const urlOk = u => { try { const p = new URL(u, location.href).protocol; return p === 'http:' || p === 'https:' ? String(u) : ''; } catch { return ''; } };
let rotaN = 0, sair = null; // rotaN: descarta respostas atrasadas; sair: limpeza ao trocar de página
const aoSair = fn => { const ant = sair; sair = () => { if (ant) ant(); fn(); }; };
const vazio = t => `<div class="vazio">${esc(t)}</div>`;
function toast(m, erro) { const d = document.createElement('div'); d.textContent = m; if (erro) d.className = 'err'; $('#toast').append(d); setTimeout(() => d.remove(), 4000); }

// Consulta o status a cada 2 s até a análise terminar. Devolve a função que para a consulta.
function acompanhar(id, aoAtualizar, aoTerminar) {
  let parar = false, t = null;
  const ciclo = async () => {
    if (parar) return;
    try {
      const s = await Api.statusProcessamento(id); if (parar) return;
      aoAtualizar(s);
      if (s.status === 'concluida' || s.status === 'falhou') return aoTerminar(s);
    } catch (e) { if (parar) return; aoAtualizar({ erroConexao: e.message }); }
    t = setTimeout(ciclo, 2000);
  };
  ciclo();
  return () => { parar = true; clearTimeout(t); };
}

/* ---------- componentes ---------- */
const cab = (t, s, extra = '') => `<header class="top"><div><h1>${t}</h1><p class="sub">${s}</p></div><div class="acts">${extra}</div></header>`;
const novaBtn = '<a class="btn pri" href="#/videos">Nova análise</a>';
function tabela(lista) {
  if (!lista.length) return vazio('Nenhuma análise encontrada.');
  return `<div class="tw"><table><thead><tr><th>ID</th><th>Vídeo</th><th>Local</th><th>Data</th><th class="n">Duração</th><th class="n">Detecções</th><th>Status</th><th class="n">Ações</th></tr></thead><tbody>${lista.map(a =>
    `<tr><td>#${esc(a.id)}</td><td>${esc(a.video)}</td><td><b>${esc(a.local)}</b></td><td>${fdata(a.data)} ${esc(a.horario || '')}</td><td class="n">${mmss(a.duracao)}</td><td class="n">${a.deteccoes ?? 0}</td><td>${tag(STATUS, a.status)}${a.status === 'processando' ? ` <small class="sub">${pct(a.progresso)}</small>` : ''}</td><td class="n">${a.id != null && a.id !== '' ? `<a href="#/analise/${encodeURIComponent(a.id)}" aria-label="Ver análise ${esc(a.id)}">Ver</a>` : '—'}</td></tr>`).join('')}</tbody></table></div>`;
}
function modal(html) { const m = $('#modal'); m.innerHTML = html; m.setAttribute('aria-labelledby', 'mt'); m.showModal(); return m; }

/* ---------- páginas ---------- */
async function pgGeral() {
  const v = $('#view'), my = rotaN, dias = [7, 30, 90].includes(+sessionStorage.dias) ? +sessionStorage.dias : 7;
  v.innerHTML = vazio('Carregando…');
  const zero = { totais: { analises: 0, deteccoes: 0, framesComPlaca: 0, pendentes: 0 }, serie: [], distribuicao: [], recentes: [] };
  const r0 = await safe(Api.dashboard(dias), zero); if (my !== rotaN) return;
  const ar = x => Array.isArray(x) ? x : [], e = r0.e;
  const d = { totais: { ...zero.totais, ...(r0.d.totais || {}) }, serie: ar(r0.d.serie), distribuicao: ar(r0.d.distribuicao), recentes: ar(r0.d.recentes) };
  const t = d.totais;
  const k = [['Análises', t.analises], ['Detecções', t.deteccoes], ['Frames com placa', t.framesComPlaca], ['Revisões pendentes', t.pendentes]];
  const max = Math.max(1, ...d.serie.map(s => s.valor));
  v.innerHTML = cab('Monitoramento de Vias Públicas', 'Acompanhamento das análises realizadas nas vias públicas.',
    `<select id="per" aria-label="Período">${[7, 30, 90].map(n => `<option value="${n}" ${n == dias ? 'selected' : ''}>Últimos ${n} dias</option>`).join('')}</select>${novaBtn}`) + aviso(e, true) +
    `<div class="grid g4">${k.map(([l, n]) => `<div class="card kpi"><small>${l}</small><b>${n}</b></div>`).join('')}</div>
    <div class="grid g2"><section class="card"><h2>Detecções ao longo do tempo</h2><div class="cb">${d.serie.some(s => s.valor) ? `<div class="bars" role="img" aria-label="Gráfico de detecções por período">${d.serie.map(s => `<div style="height:${s.valor / max * 100}%" title="${esc(s.rotulo)}: ${s.valor}"></div>`).join('')}</div><div class="lbl">${d.serie.map(s => `<span>${esc(s.rotulo)}</span>`).join('')}</div>` : vazio('Sem detecções no período.')}</div></section>
    <section class="card"><h2>Distribuição por classe</h2><div class="cb">${(d.distribuicao.length ? d.distribuicao : [{ classe: 'Placa', total: 0 }]).map(c => { const m = Math.max(1, ...d.distribuicao.map(x => x.total)); return `<div class="hb"><span>${esc(c.classe)}</span><i style="width:${c.total / m * 100}%"></i><b>${c.total}</b></div>`; }).join('')}<p class="sub">Contagem nos frames guardados (1 por segundo de vídeo).</p></div></section></div>
    <section class="card"><div class="ch"><h2>Análises recentes</h2><a href="#/analises">Ver todas</a></div>${tabela(d.recentes.slice(0, 5))}</section>`;
  $('#per').onchange = ev => { sessionStorage.dias = ev.target.value; pgGeral(); };
}

async function pgAnalises() {
  const v = $('#view'); v.innerHTML = vazio('Carregando…');
  const my = rotaN, { d, e } = await safe(Api.listarAnalises(), []); if (my !== rotaN) return;
  const est = { q: '', st: '', loc: '', pag: 1 };
  const locais = [...new Set(d.map(a => a.local))];
  v.innerHTML = cab('Análises', 'Consulte as análises de vídeo realizadas.', novaBtn) + aviso(e) +
    `<section class="card"><div class="flt"><input id="q" type="search" placeholder="Pesquisar por ID, vídeo ou local" aria-label="Pesquisar" style="flex:1;min-width:200px">
    <select id="st" aria-label="Status"><option value="">Todos os status</option>${Object.entries(STATUS).map(([k, [t]]) => `<option value="${k}">${t}</option>`).join('')}</select>
    <select id="lo" aria-label="Local"><option value="">Todos os locais</option>${locais.map(l => `<option>${esc(l)}</option>`).join('')}</select></div><div id="tb"></div><div class="pg" id="pg"></div></section>`;
  const draw = () => {
    const q = est.q.toLowerCase(), pp = Cfg.get().porPagina;
    const f = d.filter(a => (!est.st || a.status == est.st) && (!est.loc || a.local == est.loc) && `${a.id} ${a.video} ${a.local}`.toLowerCase().includes(q));
    const pgs = Math.max(1, Math.ceil(f.length / pp)); est.pag = Math.min(est.pag, pgs);
    $('#tb').innerHTML = e ? vazio('Não foi possível carregar as análises.') : tabela(f.slice((est.pag - 1) * pp, est.pag * pp));
    $('#pg').innerHTML = `<span class="sub">${f.length} registro(s)</span><button class="btn" id="pv" ${est.pag < 2 ? 'disabled' : ''}>Anterior</button><span>${est.pag} / ${pgs}</span><button class="btn" id="px" ${est.pag >= pgs ? 'disabled' : ''}>Próxima</button>`;
    $('#pv').onclick = () => { est.pag--; draw(); }; $('#px').onclick = () => { est.pag++; draw(); };
  };
  $('#q').oninput = x => { est.q = x.target.value; est.pag = 1; draw(); };
  $('#st').onchange = x => { est.st = x.target.value; est.pag = 1; draw(); };
  $('#lo').onchange = x => { est.loc = x.target.value; est.pag = 1; draw(); };
  draw();
}

function pgVideos() {
  const v = $('#view'); let arq = null, dur = 0, url = null;
  const revogar = () => { if (url) { URL.revokeObjectURL(url); url = null; } };
  aoSair(revogar);
  v.innerHTML = cab('Nova análise', `Envie um vídeo de ${CONFIG.VIDEO_MIN_S} a ${CONFIG.VIDEO_MAX_S} segundos para detecção de placas.`) +
    `<div class="grid g2"><section class="card"><h2>Vídeo</h2><div class="cb"><div class="drop" id="dz"><p>Arraste um vídeo aqui</p><button class="btn" type="button" id="pick">Selecionar arquivo</button><input id="fi" type="file" accept="video/*" hidden aria-label="Arquivo de vídeo"></div>
    <p class="er" id="er" role="alert"></p><div id="pv" hidden><video id="vp" controls style="width:100%;margin-top:12px;border-radius:6px"></video><p id="inf" class="sub"></p><button class="btn no" id="rm" type="button">Remover vídeo</button></div></div></section>
    <section class="card"><h2>Dados da gravação</h2><div class="cb"><div class="f"><label for="lc">Local *</label><input id="lc" required maxlength="150" placeholder="Ex.: Av. Higienópolis, Centro"></div>
    <div class="f"><label for="dt">Data</label><input id="dt" type="date"></div><div class="f"><label for="hr">Horário</label><input id="hr" type="time"></div>
    <div class="f"><label for="ob">Observações</label><textarea id="ob" rows="3" maxlength="2000"></textarea></div>
    <p>Estado: <span id="es" class="tag gray">Aguardando</span></p><progress id="pr" max="1" value="0" hidden></progress><p id="msg" class="sub" aria-live="polite"></p>
    <button class="btn pri" id="go" type="button">Iniciar análise</button></div></section></div>`;
  const erro = t => $('#er').textContent = t || '';
  const est = (t, c) => { $('#es').textContent = t; $('#es').className = 'tag ' + c; };
  function escolher(f) {
    erro(); if (!f) return;
    if (!CONFIG.FORMATOS.includes(f.type)) return erro('Formato não aceito. Use MP4, WebM ou MOV.');
    if (f.size > CONFIG.TAM_MAX_MB * 1048576) return erro(`O arquivo excede ${CONFIG.TAM_MAX_MB} MB.`);
    revogar(); url = URL.createObjectURL(f); const p = $('#vp'); p.src = url;
    p.onloadedmetadata = () => {
      dur = p.duration;
      if (dur < CONFIG.VIDEO_MIN_S || dur > CONFIG.VIDEO_MAX_S) { erro(`A duração (${mmss(dur)}) deve estar entre ${CONFIG.VIDEO_MIN_S}s e ${CONFIG.VIDEO_MAX_S}s.`); return limpar(); }
      arq = f; $('#pv').hidden = false; $('#inf').textContent = `${f.name} · ${f.type.split('/')[1].toUpperCase()} · ${(f.size / 1048576).toFixed(1)} MB · ${mmss(dur)}`;
    };
    p.onerror = () => { erro('Não foi possível ler o vídeo.'); limpar(); };
  }
  function limpar() { arq = null; const p = $('#vp'); p.onerror = null; p.onloadedmetadata = null; p.removeAttribute('src'); p.load(); revogar(); $('#pv').hidden = true; $('#fi').value = ''; est('Aguardando', 'gray'); }
  $('#pick').onclick = () => $('#fi').click(); $('#fi').onchange = x => escolher(x.target.files[0]); $('#rm').onclick = () => { limpar(); erro(); };
  const dz = $('#dz');
  dz.ondragover = x => { x.preventDefault(); dz.classList.add('ov'); }; dz.ondragleave = () => dz.classList.remove('ov');
  dz.ondrop = x => { x.preventDefault(); dz.classList.remove('ov'); escolher(x.dataTransfer.files[0]); };
  const trava = b => ['go', 'rm', 'pick'].forEach(i => { $('#' + i).disabled = b; });
  $('#go').onclick = async () => {
    $('#lc').removeAttribute('aria-invalid');
    if (!arq) return erro('Selecione um vídeo antes de iniciar.');
    if (!$('#lc').value.trim()) { $('#lc').setAttribute('aria-invalid', 'true'); $('#lc').focus(); return erro('Informe o local da gravação.'); }
    erro(); trava(true); est('Enviando', 'blue'); $('#pr').value = 0; $('#pr').hidden = false; $('#msg').textContent = 'Enviando o vídeo…';
    const my = rotaN;
    let r;
    try {
      r = await Api.enviarVideo(arq, { local: $('#lc').value.trim(), data: $('#dt').value, horario: $('#hr').value, observacoes: $('#ob').value.trim() }, p => $('#pr').value = p);
    } catch (x) { $('#pr').hidden = true; $('#msg').textContent = ''; est('Falhou', 'red'); erro(x.message); trava(false); return; }
    if (my !== rotaN) return;
    const link = `<a href="#/analise/${encodeURIComponent(r.id)}">Abrir análise #${esc(r.id)}</a>`;
    est('Na fila', 'gray'); $('#pr').value = 0; $('#msg').innerHTML = `Vídeo recebido. Aguardando o modelo… ${link}`;
    aoSair(acompanhar(r.id, s => {
      if (s.erroConexao) return $('#msg').innerHTML = `Sem resposta da API; tentando de novo… ${link}`;
      const st = pick(STATUS, s.status); if (st) est(st[0], st[1]);
      if (s.status === 'processando') { $('#pr').value = s.progresso || 0; $('#msg').innerHTML = `Detectando placas: ${pct(s.progresso)} · ${link}`; }
    }, s => {
      $('#pr').hidden = true;
      $('#msg').innerHTML = s.status === 'concluida'
        ? `Análise concluída. <a href="#/analise/${encodeURIComponent(r.id)}">Ver vídeo anotado e frames</a> · <button class="btn" id="nv" type="button">Enviar outro vídeo</button>`
        : `<span class="er">O processamento falhou: ${esc(s.erro || 'erro desconhecido')}</span> · <button class="btn" id="nv" type="button">Enviar outro vídeo</button>`;
      $('#nv').onclick = pgVideos;
    }));
  };
}

const TAM_MINI = 220; // largura das miniaturas de frames (px)

async function pgDetalhe(id, frameInicial) {
  const v = $('#view'); v.innerHTML = vazio('Carregando…');
  const my = rotaN, a = await safe(Api.obterAnalise(id), null); if (my !== rotaN) return;
  const voltar = '<p><a href="#/analises">← Voltar para análises</a></p>';
  if (!a.d) return v.innerHTML = voltar + cab('Análise #' + esc(id), '') + aviso(a.e) + vazio('Análise indisponível.');
  const A = a.d;
  const meta = `<section class="card meta">${[['Local', A.local], ['Data', fdata(A.data)], ['Horário', A.horario], ['Duração', mmss(A.duracao)]].map(([l, x]) => `<div><small>${l}</small><b>${esc(x || '—')}</b></div>`).join('')}</section>`;
  const topo = voltar + cab('Análise #' + esc(A.id), esc(A.video) + (A.versaoModelo ? ` · modelo ${esc(A.versaoModelo)}` : ''), tag(STATUS, A.status));

  if (A.status !== 'concluida') {   // na fila, processando ou falhou
    v.innerHTML = topo + meta + (A.status === 'falhou'
      ? `<div class="aviso" role="alert"><b>O processamento falhou:</b> ${esc(A.erro || 'erro desconhecido')}</div>`
      : `<section class="card"><h2>Processando o vídeo</h2><div class="cb"><p id="pm" class="sub" aria-live="polite">${A.status === 'na_fila' ? 'Na fila do modelo…' : 'Detectando placas: ' + pct(A.progresso)}</p><progress id="pp" max="1" value="${+A.progresso || 0}"></progress><p class="sub">Esta página atualiza sozinha quando a análise terminar.</p></div></section>`);
    if (A.status !== 'falhou') aoSair(acompanhar(A.id, s => {
      if (s.erroConexao) return $('#pm').textContent = 'Sem resposta da API; tentando de novo…';
      $('#pp').value = s.progresso || 0; $('#pm').textContent = s.status === 'na_fila' ? 'Na fila do modelo…' : 'Detectando placas: ' + pct(s.progresso);
    }, () => { if (my === rotaN) pgDetalhe(id, frameInicial); }));
    return;
  }

  const [d, fr] = await Promise.all([safe(Api.deteccoes(id), []), safe(Api.frames(id), [])]); if (my !== rotaN) return;
  let dets = d.d, sel = null, fc = '', frv = '', busy = false, atual = null, soPlaca = false, consulta = 0;
  const frames = fr.d, vurl = urlOk(Api.url(A.videoUrl)), fps = +A.fps || 30;
  const resumo = [['Detecções', A.deteccoes], ['Frames com placa', A.framesComPlaca], ['Frames guardados', A.framesGuardados], ['Intervalo entre frames', (A.intervaloFrames || 1) + ' s']];
  v.innerHTML = topo + aviso(d.e || fr.e) + meta +
    `<section class="card"><h2>Resumo da detecção</h2><div class="grid g4" style="margin:0;padding:16px">${resumo.map(([l, n]) => `<div><small class="sub">${l}</small><b style="font-size:24px;display:block">${esc(n)}</b></div>`).join('')}</div><p class="sub" style="padding:0 18px 14px">Detecções contadas nos frames guardados (1 a cada ${esc(A.intervaloFrames || 1)} s). A mesma placa pode aparecer em vários frames.</p></section>
    <div class="split"><section class="card"><div class="ch"><h2>Vídeo com as placas rotuladas</h2></div><div class="vid">${vurl ? `<video id="vp" src="${esc(vurl)}" controls preload="metadata" playsinline></video>` : '<div class="ph">Vídeo anotado não disponível.</div>'}</div>
    <div class="ctl" style="flex-wrap:wrap">${vurl ? `<a class="btn" href="${esc(Api.video(A.id, 'anotado', true))}">Baixar vídeo anotado</a><a class="btn" href="${esc(Api.video(A.id, 'original', true))}">Baixar original</a><button class="btn" id="vf" type="button">Consultar frame deste instante</button>` : ''}</div></section>
    <section class="card"><div class="ch"><h2>Detecções</h2><span class="sub" id="cn"></span></div><div class="flt"><select id="fc" aria-label="Classe"></select><select id="fr" aria-label="Revisão"><option value="">Toda revisão</option>${Object.entries(REV).map(([k, [t]]) => `<option value="${k}">${t}</option>`).join('')}</select></div><div class="dl" id="dl"></div></section></div>
    <section class="card" id="cf"><div class="ch"><h2>Consulta de frames</h2><span class="sub">${frames.length} frame(s) guardado(s) · 1 a cada ${esc(A.intervaloFrames || 1)} s</span></div>
      <form class="flt" id="fq"><label>Nº do frame <input id="qn" type="number" min="1" step="1" inputmode="numeric" style="width:120px"></label><label>ou tempo <input id="qt" placeholder="mm:ss ou s" style="width:120px"></label>
      <button class="btn pri" type="submit">Consultar</button><label><input type="checkbox" id="qp"> Só frames com placa</label></form>
      <div id="fv" class="cb">${frames.length ? vazio('Escolha um frame abaixo ou consulte pelo número ou tempo.') : vazio(fr.e ? 'Não foi possível carregar os frames.' : 'Nenhum frame guardado.')}</div>
      <div class="tira" id="tira" aria-label="Frames guardados"></div></section>`;

  const vp = $('#vp');
  const lista = () => soPlaca ? frames.filter(f => f.qtdPlacas > 0) : frames;
  const maisProximo = n => lista().reduce((m, f) => !m || Math.abs(f.numero - n) < Math.abs(m.numero - n) ? f : m, null);
  const tempoParaFrame = t => Math.floor(t * fps + 1e-6) + 1;
  const lerTempo = s => { s = String(s).trim().replace(',', '.').replace(/s$/i, ''); const p = s.split(':'); if (p.length > 2 || p.some(x => x === '' || isNaN(+x))) return NaN; return p.length === 2 ? +p[0] * 60 + +p[1] : +p[0]; };

  function tira() {
    const l = lista();
    $('#tira').innerHTML = l.length ? l.map(f => `<button type="button" class="mini ${f.numero === atual ? 'on' : ''}" data-n="${f.numero}" aria-label="Frame ${f.numero}, ${mmss(f.tempo)}, ${f.qtdPlacas} placa(s)"><img loading="lazy" alt="" src="${esc(Api.imagemFrame(A.id, f.numero, 'anotado', TAM_MINI))}"><span>#${f.numero} · ${mmss(f.tempo)}${f.qtdPlacas ? ` · <b>${f.qtdPlacas}</b>` : ''}</span></button>`).join('') : vazio('Nenhum frame com placa.');
  }
  async function consultar(n, nota = '') {
    const f = maisProximo(n); if (!f) return toast('Nenhum frame disponível para consulta.', true);
    if (f.numero !== n) nota = `O frame ${n} não foi guardado (só 1 a cada ${A.intervaloFrames || 1} s). Mostrando o mais próximo.`;
    const meu = ++consulta; atual = f.numero; tira();
    const el = $(`#tira [data-n="${f.numero}"]`); if (el) el.scrollIntoView({ block: 'nearest', inline: 'center' });
    history.replaceState(null, '', `#/analise/${encodeURIComponent(A.id)}/frame/${f.numero}`);
    $('#fv').innerHTML = vazio('Carregando frame…');
    const r = await safe(Api.frame(A.id, f.numero), null); if (meu !== consulta || my !== rotaN) return;
    if (!r.d) return $('#fv').innerHTML = aviso(r.e) + vazio('Frame indisponível.');
    const F = r.d, l = lista(), i = l.findIndex(x => x.numero === F.numero), o = urlOk(Api.url(F.originalUrl)), an = urlOk(Api.url(F.anotadoUrl));
    $('#fv').innerHTML = (nota ? `<p class="sub" role="status">${esc(nota)}</p>` : '') +
      `<div class="fbar"><button class="btn" type="button" id="fa" ${i <= 0 ? 'disabled' : ''}>◀ Anterior</button><b>Frame ${F.numero} · ${mmss(F.tempo)} <small class="sub">(${(+F.tempo).toFixed(2)} s)</small></b><button class="btn" type="button" id="fp" ${i < 0 || i >= l.length - 1 ? 'disabled' : ''}>Próximo ▶</button>${vp ? '<button class="btn" type="button" id="fvid">Ver no vídeo</button>' : ''}</div>
      <div class="cmp"><figure><figcaption>Original</figcaption><a href="${esc(o)}" target="_blank" rel="noopener"><img src="${esc(o)}" alt="Frame ${F.numero} original"></a></figure>
      <figure><figcaption>Rotulado · ${F.deteccoes.length} placa(s)</figcaption><a href="${esc(an)}" target="_blank" rel="noopener"><img src="${esc(an)}" alt="Frame ${F.numero} com as placas rotuladas"></a></figure></div>
      ${F.deteccoes.length ? `<div class="tw"><table><thead><tr><th>Detecção</th><th>Classe</th><th class="n">Confiança</th><th>Caixa (px)</th><th>Revisão</th></tr></thead><tbody>${F.deteccoes.map(x => `<tr><td>#${esc(x.id)}</td><td><b>${esc(x.classeCorrigida || x.classe)}</b></td><td class="n">${Math.round(x.confianca * 100)}%</td><td><small>${x.bbox.x_min},${x.bbox.y_min} – ${x.bbox.x_max},${x.bbox.y_max}</small></td><td>${tag(REV, x.revisao || 'pendente')}</td></tr>`).join('')}</tbody></table></div>` : '<p class="sub">Nenhuma placa detectada neste frame.</p>'}`;
    $('#fa').onclick = () => consultar(l[i - 1].numero); $('#fp').onclick = () => consultar(l[i + 1].numero);
    if ($('#fvid')) $('#fvid').onclick = () => { vp.currentTime = F.tempo; vp.pause(); vp.scrollIntoView({ block: 'center' }); };
  }
  $('#fq').onsubmit = ev => {
    ev.preventDefault();
    const n = $('#qn').value.trim(), t = $('#qt').value.trim();
    if (n) { if (!/^\d+$/.test(n) || +n < 1) return toast('Número de frame inválido.', true); return consultar(+n); }
    if (t) { const s = lerTempo(t); if (!(s >= 0)) return toast('Tempo inválido. Use mm:ss ou segundos.', true); return consultar(tempoParaFrame(s)); }
    toast('Informe o número do frame ou o tempo.', true);
  };
  $('#qp').onchange = x => { soPlaca = x.target.checked; tira(); if (atual) consultar(atual); };
  $('#tira').onclick = ev => { const b = ev.target.closest('.mini'); if (b) consultar(+b.dataset.n); };
  if (vp) { $('#vf').onclick = () => { vp.pause(); consultar(tempoParaFrame(vp.currentTime)); $('#cf').scrollIntoView({ behavior: 'smooth', block: 'start' }); }; vp.onerror = () => toast('Não foi possível carregar o vídeo.', true); }

  const listar = () => {
    const f = dets.filter(x => (!fc || x.classe == fc) && (!frv || x.revisao == frv));
    $('#cn').textContent = f.length + ' registro(s)';
    $('#dl').innerHTML = f.length ? f.map(x => `<div class="di ${x.id == sel ? 'on' : ''}" data-i="${esc(x.id)}" tabindex="0"><div class="r"><span>${mmss(x.tempo)} · frame ${esc(x.frame)} <b>${esc(x.classeCorrigida || x.classe)}</b></span><span>${Math.round(x.confianca * 100)}%</span></div>
      ${x.classeCorrigida ? `<small class="sub">IA previu: ${esc(x.classe)}</small><br>` : ''}${tag(REV, x.revisao || 'pendente')}${x.obs ? `<small class="sub"> ${esc(x.obs)}</small>` : ''}
      <div class="a"><button class="btn ok" data-a="confirmar">Confirmar</button><button class="btn no" data-a="rejeitar">Rejeitar</button><button class="btn" data-a="corrigir">Corrigir</button></div></div>`).join('') : vazio(d.e ? 'Não foi possível carregar as detecções.' : 'Nenhuma detecção encontrada.');
  };
  const classes = () => [...new Set([...Cfg.get().classes, ...dets.map(x => x.classe)])];
  $('#fc').innerHTML = '<option value="">Todas as classes</option>' + classes().map(c => `<option>${esc(c)}</option>`).join('');
  $('#fc').onchange = x => { fc = x.target.value; listar(); }; $('#fr').onchange = x => { frv = x.target.value; listar(); };
  async function revisar(x, acao, corpo) {
    if (busy) return false; busy = true;
    try { const n = await Api.revisar(A.id, x.id, acao, corpo); if (!pick(REV, n.revisao)) throw new Error('A API não confirmou o novo estado da revisão.');
      dets = dets.map(y => y.id == x.id ? { ...y, ...n } : y); listar(); if (atual === x.frame) consultar(atual); toast('Revisão registrada.'); return true; }
    catch (er) { toast('Não foi possível salvar: ' + er.message, true); return false; }
    finally { busy = false; }
  }
  $('#dl').onkeydown = ev => { if ((ev.key === 'Enter' || ev.key === ' ') && ev.target.classList.contains('di')) { ev.preventDefault(); ev.target.click(); } };
  $('#dl').onclick = ev => {
    const it = ev.target.closest('.di'); if (!it) return; const x = dets.find(y => y.id == it.dataset.i), ac = ev.target.dataset.a;
    if (!ac) { sel = x.id; listar(); if (vp) { vp.pause(); vp.currentTime = x.tempo; } consultar(x.frame); return; }
    if (ac == 'corrigir') {
      const m = modal(`<h2 id="mt">Corrigir detecção</h2><p class="sub">Classe original da IA: <b>${esc(x.classe)}</b></p><div class="f"><label for="nc">Nova classe</label><select id="nc">${classes().map(c => `<option ${c == (x.classeCorrigida || x.classe) ? 'selected' : ''}>${esc(c)}</option>`).join('')}</select></div><div class="f"><label for="nj">Justificativa</label><textarea id="nj" rows="3"></textarea></div><p class="er" id="me" role="alert"></p><div class="acts"><button class="btn pri" id="sv">Salvar correção</button><button class="btn" id="cc">Cancelar</button></div>`);
      $('#cc').onclick = () => m.close();
      $('#sv').onclick = async () => {
        const nc = $('#nc').value; if (!nc || nc === (x.classeCorrigida || x.classe)) return $('#me').textContent = 'Escolha uma classe diferente da atual ou cancele. (Adicione classes em Configurações.)';
        $('#sv').disabled = true; if (await revisar(x, 'corrigir', { classe: nc, obs: $('#nj').value.trim() })) m.close(); else $('#sv').disabled = false;
      };
    } else revisar(x, ac, {});
  };
  listar(); tira();
  if (frameInicial) consultar(frameInicial);
}

async function pgRelatorios() {
  const v = $('#view'), zero = { analises: 0, porClasse: [], revisao: { confirmadas: 0, rejeitadas: 0, corrigidas: 0, pendentes: 0 } };
  const q = { de: '', ate: '', local: '' };
  v.innerHTML = cab('Relatórios', 'Resumo dos resultados com base nos filtros.', '<button class="btn" id="csv">Exportar CSV</button>') +
    `<div class="flt card"><label>De <input type="date" id="de"></label><label>Até <input type="date" id="at"></label><input id="lo" placeholder="Local" aria-label="Local"><button class="btn pri" id="ap">Aplicar</button></div><div id="rel"></div>`;
  let R = zero, n = 0, ok = false;
  async function carregar() {
    const meu = ++n, my = rotaN, { d, e } = await safe(Api.relatorio(Object.fromEntries(Object.entries(q).filter(([, x]) => x))), zero);
    if (meu !== n || my !== rotaN) return; ok = !e;
    R = { ...zero, ...d }; const r = { ...zero.revisao, ...R.revisao }, tot = r.confirmadas + r.rejeitadas + r.corrigidas + r.pendentes, pc = n => tot ? Math.round(n / tot * 100) + '%' : '0%';
    $('#rel').innerHTML = aviso(e, true) + `<div class="grid g4">${[['Análises', R.analises], ['Confirmadas', pc(r.confirmadas)], ['Rejeitadas', pc(r.rejeitadas)], ['Corrigidas', pc(r.corrigidas)]].map(([l, n]) => `<div class="card kpi"><small>${l}</small><b>${n}</b></div>`).join('')}</div>
    <div class="grid g2"><section class="card"><h2>Detecções por classe</h2>${R.porClasse.length ? `<table><tbody>${R.porClasse.map(c => `<tr><td>${esc(c.classe)}</td><td class="n">${c.total}</td></tr>`).join('')}</tbody></table>` : vazio('Sem dados. Total: 0')}</section>
    <section class="card"><h2>Situação das revisões</h2><table><tbody>${Object.entries({ confirmada: r.confirmadas, rejeitada: r.rejeitadas, corrigida: r.corrigidas, pendente: r.pendentes }).map(([k, v]) => `<tr><td>${tag(REV, k)}</td><td class="n">${v}</td></tr>`).join('')}</tbody></table></section></div>`;
  }
  $('#ap').onclick = () => { if ($('#de').value && $('#at').value && $('#de').value > $('#at').value) return toast('A data inicial não pode ser posterior à final.', true); q.de = $('#de').value; q.ate = $('#at').value; q.local = $('#lo').value.trim(); carregar(); };
  const cel = x => { if (typeof x === 'number') return x; let t = String(x ?? ''); if (/^[=+\-@\t\r]/.test(t)) t = "'" + t; return '"' + t.replace(/"/g, '""') + '"'; }; // evita fórmulas em planilhas
  $('#csv').onclick = () => {
    if (!ok) return toast('Os dados não foram carregados; não há o que exportar.', true);
    const r = { ...zero.revisao, ...R.revisao };
    const L = [['secao', 'item', 'valor'], ['filtro', 'data_inicial', q.de], ['filtro', 'data_final', q.ate], ['filtro', 'local', q.local], ['resumo', 'analises', +R.analises || 0],
      ...Object.entries(r).map(([k, n]) => ['revisao', k, +n || 0]), ...R.porClasse.map(c => ['deteccoes_por_classe', c.classe, +c.total || 0])];
    const b = new Blob(['﻿' + L.map(l => l.map(cel).join(';')).join('\r\n')], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = 'relatorio.csv'; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  };
  carregar();
}

async function pgConfig() {
  const c = Cfg.get(), v = $('#view'), my = rotaN;
  v.innerHTML = cab('Configurações', 'Preferências de exibição.') + `<section class="card"><div class="cb">
  <div class="f"><label for="pp">Registros por página</label><select id="pp">${[5, 10, 25, 50].map(n => `<option ${n == c.porPagina ? 'selected' : ''}>${n}</option>`).join('')}</select></div>
  <div class="f"><label for="cl">Classes disponíveis para correção e filtros (separadas por vírgula)</label><input id="cl" value="${esc(c.classes.join(', '))}"></div>
  <button class="btn pri" id="sv">Salvar preferências</button><hr><p>Versão: v0.2.0</p><p>API: <code>${esc(CONFIG.API_URL)}</code> — <span id="ap" class="tag gray">Verificando…</span></p><p class="sub" id="ai"></p></div></section>`;
  $('#sv').onclick = () => {
    const cl = [...new Set($('#cl').value.split(',').map(x => x.trim()).filter(Boolean))];
    if (!cl.length || cl.some(x => x.length > 40)) return toast('Informe ao menos uma classe (máx. 40 caracteres cada).', true);
    Cfg.set({ porPagina: +$('#pp').value, classes: cl }) ? toast('Preferências salvas.') : toast('Não foi possível salvar neste navegador.', true);
  };
  const r = await safe(Api.saude(), null); if (my !== rotaN) return; $('#ap').textContent = r.e ? 'Desconectada' : 'Conectada'; $('#ap').className = 'tag ' + (r.e ? 'red' : 'green');
  if (r.d) $('#ai').textContent = `Banco: conectado · Modelo: ${r.d.modelo} (classes: ${(r.d.classes || []).join(', ')}) · 1 frame guardado a cada ${r.d.intervaloFrames} s`;
  else if (r.e) $('#ai').textContent = r.e;
}

/* ---------- roteador ---------- */
const naoEncontrada = () => { $('#view').innerHTML = cab('Página não encontrada', 'O endereço informado não existe.', '<a class="btn" href="#/">Ir para a Visão Geral</a>'); };
function rota() {
  if (sair) { const s = sair; sair = null; s(); } rotaN++;
  const [, r = '', p, extra, n] = (location.hash || '#/').slice(1).split('/');
  document.querySelectorAll('nav a').forEach(a => { const on = a.dataset.r == (r == 'analise' ? 'analises' : r); a.classList.toggle('on', on); on ? a.setAttribute('aria-current', 'page') : a.removeAttribute('aria-current'); });
  const m = { '': pgGeral, analises: pgAnalises, videos: pgVideos, relatorios: pgRelatorios, configuracoes: pgConfig };
  let id = ''; try { id = decodeURIComponent(p || '').trim(); } catch { id = ''; }
  const frame = extra === 'frame' && /^\d+$/.test(n || '') ? +n : null;   // #/analise/<id>/frame/<n>
  if (r == 'analise') id ? pgDetalhe(id, frame) : naoEncontrada(); else (Object.hasOwn(m, r) ? m[r] : naoEncontrada)();
  $('#view').focus(); window.scrollTo(0, 0);
}
$('#skip').addEventListener('click', e => { e.preventDefault(); $('#view').focus(); }); // não altera a rota
addEventListener('hashchange', rota); rota();
