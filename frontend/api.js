/* Camada de serviços — única parte do front que fala com o back-end (backend/api/api.py).
   Rotas e formatos: docs/04_API.md.

   Endereço da API:
   - aberto pela própria API (http://127.0.0.1:8000): usa a mesma origem, '/api';
   - aberto pelo Live Server (porta 5500/5501) ou como arquivo: usa http://127.0.0.1:8000/api;
   - para outro endereço, defina window.API_URL antes de carregar este arquivo. */
const CONFIG = (() => {
  const mesmaOrigem = /^https?:$/.test(location.protocol) && !['5500', '5501'].includes(location.port);
  const API_URL = (window.API_URL || (mesmaOrigem ? '/api' : 'http://127.0.0.1:8000/api')).replace(/\/$/, '');
  return {
    API_URL, ORIGEM: new URL(API_URL, location.href).origin,
    VIDEO_MIN_S: 10, VIDEO_MAX_S: 40,                    // duração aceita (igual ao backend/.env)
    FORMATOS: ['video/mp4', 'video/webm', 'video/quicktime'], TAM_MAX_MB: 200
  };
})();

async function req(caminho, opcoes) {
  let r;
  try { r = await fetch(CONFIG.API_URL + caminho, opcoes); }
  catch { throw new Error('Sem conexão com a API.'); }
  let corpo = null; try { corpo = await r.json(); } catch { corpo = null; }
  if (!r.ok) throw new Error((corpo && corpo.error) || ('A API respondeu com erro ' + r.status + '.'));
  if (corpo === null) throw new Error('Resposta inválida da API.');
  return corpo;
}
// Uma resposta com formato errado vira erro; nunca é convertida em "dados vazios".
const exigir = (d, lista) => {
  if (lista ? !Array.isArray(d) : !(d && typeof d === 'object' && !Array.isArray(d))) throw new Error('Resposta inválida da API.');
  return d;
};
const obj = (c, o) => req(c, o).then(d => exigir(d, false));
const arr = (c, o) => req(c, o).then(d => exigir(d, true));
// Content-Type só em JSON; no upload multipart o navegador define o boundary.
const post = corpo => ({ method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corpo) });
const eid = encodeURIComponent;

const Api = {
  // Converte os caminhos devolvidos pela API (/api/...) em URL completa (vídeos e imagens).
  url: caminho => caminho ? new URL(caminho, CONFIG.ORIGEM).href : '',
  // → { totais:{analises,deteccoes,framesComPlaca,pendentes}, serie:[{rotulo,valor}], distribuicao:[{classe,total}], recentes:[Analise] }
  dashboard: dias => obj('/dashboard?dias=' + eid(dias)),
  // Analise: { id, video, local, data, horario, observacoes, duracao(s), fps, largura, altura,
  //            status:'na_fila|processando|concluida|falhou', progresso(0-1), erro,
  //            deteccoes, framesComPlaca, framesGuardados, intervaloFrames(s), modelo, versaoModelo,
  //            videoUrl (vídeo ANOTADO), videoOriginalUrl }
  listarAnalises: () => arr('/analises'),
  obterAnalise: id => obj('/analises/' + eid(id)),
  statusProcessamento: id => obj('/analises/' + eid(id) + '/status'), // → { status, progresso, erro }
  // Deteccao: { id, frame, tempo(s), classe, confianca(0-1), revisao:'pendente|confirmada|rejeitada|corrigida',
  //             classeCorrigida, obs, bbox:{x_min,y_min,x_max,y_max} (pixels), caixa:{x,y,l,a} (0-1) }
  deteccoes: id => arr('/analises/' + eid(id) + '/deteccoes'),
  // Frames guardados (1 a cada intervaloFrames s): [{ numero, tempo, qtdPlacas, originalUrl, anotadoUrl }]
  frames: id => arr('/analises/' + eid(id) + '/frames'),
  // Um frame: { numero, tempo, originalUrl, anotadoUrl, deteccoes:[Deteccao] }
  frame: (id, numero) => obj('/analises/' + eid(id) + '/frames/' + eid(numero)),
  // URL da imagem de um frame: versao 'original' | 'anotado'; largura opcional (miniatura)
  imagemFrame: (id, numero, versao, largura) => Api.url('/api/analises/' + eid(id) + '/frames/' + eid(numero) +
    '/imagem?versao=' + eid(versao) + (largura ? '&largura=' + eid(largura) : '')),
  // URL do vídeo: versao 'anotado' | 'original'; download=true para baixar o arquivo
  video: (id, versao, download) => Api.url('/api/analises/' + eid(id) + '/video?versao=' + eid(versao) + (download ? '&download=1' : '')),
  // acao: 'confirmar' | 'rejeitar' | 'corrigir' ; corpo: { classe?, obs? } → Deteccao atualizada
  revisar: (id, detId, acao, corpo) => obj('/analises/' + eid(id) + '/deteccoes/' + eid(detId) + '/' + acao, post(corpo)),
  // → { analises, porClasse:[{classe,total}], revisao:{confirmadas,rejeitadas,corrigidas,pendentes} }
  relatorio: q => obj('/relatorios?' + new URLSearchParams(q)),
  saude: () => obj('/saude'),
  // Upload com progresso real de envio (XHR). O processamento é acompanhado depois por statusProcessamento.
  enviarVideo(arquivo, meta, aoProgredir) {
    return new Promise((ok, falha) => {
      const x = new XMLHttpRequest(), fd = new FormData();
      fd.append('video', arquivo); Object.entries(meta).forEach(([k, v]) => v && fd.append(k, v));
      x.open('POST', CONFIG.API_URL + '/analises');
      x.upload.onprogress = e => e.lengthComputable && aoProgredir(e.loaded / e.total);
      x.onload = () => {
        let r = null; try { r = JSON.parse(x.responseText); } catch { r = null; }
        if (x.status >= 300) return falha(new Error((r && r.error) || ('A API respondeu com erro ' + x.status + '.')));
        (r && r.id != null && r.id !== '') ? ok(r) : falha(new Error('A API não retornou o identificador da análise.'));
      };
      x.onerror = () => falha(new Error('Sem conexão com a API.'));
      x.ontimeout = () => falha(new Error('Tempo de envio esgotado.'));
      x.send(fd);
    });
  }
};
