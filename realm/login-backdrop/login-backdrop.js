// Leyline login backdrop: the flat Leyline look (a dark background and the mark: the swirl turns, the
// crystal stays upright) behind the game canvas while the client shows its login screen, in place of
// the 3D gate.
//
// How it fits together:
//   * The page puts `login_backdrop: "page"` in `window.__wenilla_env`. The Leyline client patch
//     (realm/patches/0004-openvanilla-login-backdrop.patch) then skips the UI_MainMenu scene on the
//     login screen and configures the canvas with premultiplied alpha, so everything behind the
//     login form is transparent and the backdrop shows through.
//   * With `spin: { swirl, crystal }` (the two layers of the mark, as www/game.html passes them) the
//     mark is the CSS spinner: no video at all. Without it (the realm's page) a short loop of the same
//     scene plays (login-backdrop.mp4, or its VP9 copy) over its still poster (login-backdrop.webp).
//   * This module shows the backdrop only while the bridge reports `state === "login"`, and pauses
//     it everywhere else, so nothing decodes or turns while you play.
//   * A client without the patch keeps an opaque canvas: the video sits hidden behind it and the
//     old gate shows. Nothing breaks either way.
//
// Lightweight on purpose: a 7 KB poster, a 0.1 MB loop (tools/make_leyline_backdrops.py writes all
// three). Reduced-motion and Data Saver users get the mark at rest: the poster, or a spinner that stays still.

const STYLE_ID = 'ow-login-backdrop-style';

export function installLoginBackdrop(wenilla, { base = './', canvasId = 'benilla', spin = null } = {}) {
  if (document.getElementById('ow-login-backdrop')) return null;

  if (!document.getElementById(STYLE_ID)) {
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
      #ow-login-backdrop { position: fixed; inset: 0; z-index: 0; overflow: hidden; pointer-events: none;
        background: #05040c url("${base}login-backdrop.webp") center / cover no-repeat;
        transition: opacity .6s ease, visibility 0s; }
      #ow-login-backdrop.is-hidden { opacity: 0; visibility: hidden; transition: opacity .6s ease, visibility 0s .6s; }
      #ow-login-backdrop video { width: 100%; height: 100%; object-fit: cover; display: block; }
      #ow-login-backdrop.ly-flat { background: radial-gradient(circle at 50% 31.5%, rgba(70,80,200,.2) 0, rgba(70,80,200,0) min(28vh,32vw)), #080a14; }
      #ow-login-backdrop .ly-spin { position: absolute; left: 50%; top: 31.5%; width: min(35vh, 40vw); height: min(35vh, 40vw);
        transform: translate(-50%, -50%); }
      #ow-login-backdrop .ly-spin > img { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
      #ow-login-backdrop .ly-swirl { animation: ow-ly-swirl 7s linear infinite; transform-origin: 50% 50%; }
      #ow-login-backdrop.is-hidden .ly-swirl { animation-play-state: paused; }
      @keyframes ow-ly-swirl { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      @media (prefers-reduced-motion: reduce) { #ow-login-backdrop .ly-swirl { animation: none; } }
      #${canvasId} { position: relative; z-index: 1; }`;
    document.head.append(style);
  }

  const box = document.createElement('div');
  box.id = 'ow-login-backdrop';
  box.setAttribute('aria-hidden', 'true');

  const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const saveData = navigator.connection?.saveData === true;
  let video = null;
  if (spin?.swirl && spin?.crystal) {
    // the CSS spinner: the swirl turns (still under reduced motion), the crystal never does
    box.classList.add('ly-flat');
    const mark = document.createElement('span');
    mark.className = 'ly-spin';
    for (const [cls, src] of [['ly-swirl', spin.swirl], ['ly-crystal', spin.crystal]]) {
      const img = document.createElement('img');
      img.className = cls;
      img.src = src;
      img.alt = '';
      img.decoding = 'async';
      mark.append(img);
    }
    box.append(mark);
  } else if (!reduceMotion && !saveData) {
    video = document.createElement('video');
    video.muted = true; // required for autoplay
    video.defaultMuted = true;
    video.loop = true;
    video.playsInline = true;
    video.autoplay = true;
    video.preload = 'auto';
    video.poster = `${base}login-backdrop.webp`;
    video.disablePictureInPicture = true;
    video.setAttribute('muted', '');
    video.setAttribute('playsinline', '');
    // H.264 first (1.3 MB, plays almost everywhere), VP9 for browsers built without H.264
    // (open-source Chromium on some Linux distributions). The browser downloads only the one it picks.
    for (const [file, type] of [['login-backdrop.mp4', 'video/mp4; codecs="avc1.640028"'], ['login-backdrop.webm', 'video/webm; codecs="vp9"']]) {
      const src = document.createElement('source');
      src.src = base + file;
      src.type = type;
      video.append(src);
    }
    // A source the browser can't play fires `error` and the next is tried; only when the last one
    // fails too does the video go, leaving the poster, which is already the background.
    video.lastElementChild.addEventListener('error', () => video.remove());
    box.append(video);
  }

  const canvas = document.getElementById(canvasId);
  if (canvas && canvas.parentNode) canvas.parentNode.insertBefore(box, canvas);
  else document.body.prepend(box);

  let onLogin = true; // the client starts at the login screen
  const sync = () => {
    box.classList.toggle('is-hidden', !onLogin);
    if (!video) return;
    if (onLogin && !document.hidden) video.play().catch(() => {});
    else video.pause();
  };

  wenilla?.on?.('state', (s) => {
    const now = s?.state === 'login';
    if (now !== onLogin) {
      onLogin = now;
      sync();
    }
  });
  document.addEventListener('visibilitychange', sync);
  sync();
  return box;
}
