(function () {
var W = 64, H = 64;
Project.texture_width = W;
Project.texture_height = H;
Project.name = '十字弩';
Project.geckolib_modid = 'hexalunar_calamity';
Project.geckolib_model_type = 'item';

Outliner.root.slice().forEach(function (n) { if (n.remove) n.remove(); });
Cube.all.slice().forEach(function (c) { if (c.remove) c.remove(); });
Group.all.slice().forEach(function (g) { if (g.remove) g.remove(); });
Texture.all.slice().forEach(function (t) { if (t.remove) t.remove(); });

var px = new Uint8ClampedArray(W * H * 4);
function hex2rgb(h) {
  return [parseInt(h.substr(1, 2), 16), parseInt(h.substr(3, 2), 16), parseInt(h.substr(5, 2), 16)];
}
function put(x, y, c, a) {
  if (x < 0 || y < 0 || x >= W || y >= H) return;
  var i = (y * W + x) * 4;
  var al = a === undefined ? 255 : a;
  px[i] = px[i] * (1 - al / 255) + c[0] * (al / 255);
  px[i + 1] = px[i + 1] * (1 - al / 255) + c[1] * (al / 255);
  px[i + 2] = px[i + 2] * (1 - al / 255) + c[2] * (al / 255);
  px[i + 3] = 255;
}
function fill(x, y, w, h, c) {
  for (var j = y; j < y + h; j++) for (var i = x; i < x + w; i++) put(i, j, c);
}
function vgrad(x, y, w, h, c1, c2) {
  for (var j = 0; j < h; j++) {
    var t = h === 1 ? 0 : j / (h - 1);
    var c = [c1[0] + (c2[0] - c1[0]) * t, c1[1] + (c2[1] - c1[1]) * t, c1[2] + (c2[2] - c1[2]) * t];
    for (var i = 0; i < w; i++) put(x + i, y + j, c);
  }
}
function speck(x, y, w, h, c, prob, seed) {
  var s = seed;
  for (var j = 0; j < h; j++) for (var i = 0; i < w; i++) {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    if ((s % 1000) / 1000 < prob) put(x + i, y + j, c);
  }
}
function noisify(x, y, w, h, amp, seed) {
  var s = seed;
  for (var j = 0; j < h; j++) for (var i = 0; i < w; i++) {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    var d = (((s % 2000) / 1000) - 1) * amp;
    var idx = ((y + j) * W + (x + i)) * 4;
    px[idx] += d; px[idx + 1] += d; px[idx + 2] += d;
  }
}
function outline(x, y, w, h, c) {
  for (var i = 0; i < w; i++) { put(x + i, y, c); put(x + i, y + h - 1, c); }
  for (var j = 0; j < h; j++) { put(x, y + j, c); put(x + w - 1, y + j, c); }
}

fill(0, 0, W, H, hex2rgb('#0a0a0c'));

var PAL = {
  body_main: '#1a1a20', body_hi: '#2c2c34', body_dark: '#0e0e12', metal: '#45454e',
  rubber: '#121216', string: '#cfc6ad', glass: '#2e6d8e', steel: '#7c7c88',
  limb: '#17171b', cam: '#2a2a31', limb_hi: '#37373f', accent: '#8a1e1e',
  scope_body: '#1e1e24', bolt: '#4a4a52', glass_dk: '#16384a', white: '#a8a8b0'
};
var keys = Object.keys(PAL);
var i2, j2;
for (i2 = 0; i2 < keys.length; i2++) {
  var kx = (i2 % 8) * 8, ky = Math.floor(i2 / 8) * 8;
  fill(kx, ky, 8, 8, hex2rgb(PAL[keys[i2]]));
  noisify(kx, ky, 8, 8, 5, 7 + i2 * 13);
}

var C_BLACK = hex2rgb('#0a0a0c');
var C_LINE = hex2rgb('#000000');
var C_HI = hex2rgb('#3a3a44');
var C_LO = hex2rgb('#08080a');

fill(0, 16, 11, 5, hex2rgb('#1c1c22'));
vgrad(0, 16, 11, 2, hex2rgb('#26262e'), hex2rgb('#1c1c22'));
fill(0, 20, 11, 1, hex2rgb('#101014'));
for (i2 = 1; i2 <= 9; i2 += 2) { fill(i2, 17, 1, 3, hex2rgb('#0b0b0e')); }
fill(2, 18, 2, 1, hex2rgb('#5a5a66'));
fill(8, 18, 1, 1, hex2rgb('#5a5a66'));
outline(0, 16, 11, 5, C_LINE);

fill(12, 16, 5, 5, hex2rgb('#181820'));
vgrad(12, 16, 5, 2, hex2rgb('#24242c'), hex2rgb('#181820'));
fill(12, 20, 5, 1, hex2rgb('#0d0d11'));
fill(13, 19, 3, 1, hex2rgb('#3d3d47'));
outline(12, 16, 5, 5, C_LINE);

fill(18, 16, 5, 5, hex2rgb('#131319'));
fill(20, 17, 1, 3, hex2rgb('#2e2e36'));
outline(18, 16, 5, 5, C_LINE);

fill(24, 16, 2, 11, hex2rgb('#3c3c45'));
for (j2 = 0; j2 < 11; j2 += 2) { fill(24, 16 + j2, 2, 1, hex2rgb('#5d5d69')); }
outline(24, 16, 2, 11, C_LINE);

fill(28, 16, 4, 5, hex2rgb('#22222a'));
vgrad(28, 16, 2, 5, hex2rgb('#2a2a33'), hex2rgb('#16161c'));
for (j2 = 0; j2 < 5; j2 += 2) { fill(28, 16 + j2, 4, 1, hex2rgb('#101015')); }
outline(28, 16, 4, 5, C_LINE);

fill(33, 16, 4, 2, hex2rgb('#1d1d24'));
fill(33, 17, 4, 1, hex2rgb('#0f0f13'));
outline(33, 16, 4, 2, C_LINE);

fill(38, 16, 3, 6, hex2rgb('#141418'));
speck(38, 16, 3, 6, hex2rgb('#24242a'), 0.45, 99);
speck(38, 16, 3, 6, hex2rgb('#0a0a0c'), 0.35, 1234);
outline(38, 16, 3, 6, C_LINE);

vgrad(42, 16, 7, 2, hex2rgb('#2a2a32'), hex2rgb('#141419'));
fill(42, 16, 1, 2, hex2rgb('#4a4a55'));
fill(45, 16, 1, 2, hex2rgb('#4a4a55'));
fill(48, 16, 1, 2, hex2rgb('#4a4a55'));
outline(42, 16, 7, 2, C_LINE);

fill(50, 16, 3, 3, hex2rgb('#31313a'));
fill(51, 16, 1, 3, hex2rgb('#15151a'));
fill(50, 17, 3, 1, hex2rgb('#15151a'));
put(50, 16, hex2rgb('#6a6a76'));
put(52, 18, hex2rgb('#6a6a76'));
outline(50, 16, 3, 3, C_LINE);

vgrad(54, 16, 9, 2, hex2rgb('#26262d'), hex2rgb('#101014'));
fill(54, 16, 9, 1, hex2rgb('#33333c'));
fill(54, 17, 9, 1, hex2rgb('#0d0d10'));
outline(54, 16, 9, 2, C_LINE);

vgrad(0, 22, 14, 1, hex2rgb('#5b5b66'), hex2rgb('#33333b'));
fill(0, 22, 2, 1, hex2rgb('#8a8a96'));

fill(16, 22, 4, 3, hex2rgb('#20202a'));
vgrad(16, 22, 4, 1, hex2rgb('#2c2c36'), hex2rgb('#20202a'));
fill(16, 24, 4, 1, hex2rgb('#121218'));
for (i2 = 1; i2 < 4; i2++) { fill(16 + i2, 23, 1, 1, hex2rgb('#0e0e12')); }
outline(16, 22, 4, 3, C_LINE);

fill(21, 22, 4, 11, hex2rgb('#1d1d23'));
vgrad(21, 22, 4, 2, hex2rgb('#2a2a32'), hex2rgb('#1d1d23'));
for (j2 = 0; j2 < 11; j2 += 3) { fill(21, 22 + j2, 4, 1, hex2rgb('#101015')); }
fill(22, 26, 2, 3, hex2rgb('#0c0c10'));
outline(21, 22, 4, 11, C_LINE);

fill(52, 20, 3, 2, hex2rgb('#4c9ec4'));
vgrad(52, 20, 3, 2, hex2rgb('#7fc6e4'), hex2rgb('#245f80'));
put(52, 20, hex2rgb('#d8f2ff'));

var tex = new Texture({ name: 'crossbow', width: W, height: H, particle: false });
tex.add();
tex.uv_width = W;
tex.uv_height = H;
if (tex.canvas) { tex.canvas.width = W; tex.canvas.height = H; }
var img = tex.ctx.createImageData(W, H);
img.data.set(px);
tex.ctx.putImageData(img, 0, 0);
tex.update && tex.update();
tex.applyTexture && tex.setAsDefaultTexture();
if (typeof updateTextureCanvas === 'function') updateTextureCanvas(tex);

var MAT = {};
keys.forEach(function (name, idx) {
  MAT[name] = [(idx % 8) * 8 + 4, Math.floor(idx / 8) * 8 + 4, 1, 1];
});
var FACE = {
  panel: [0, 16, 11, 5], riser: [12, 16, 5, 5], riserN: [18, 16, 5, 5],
  railTop: [24, 16, 2, 11], mag: [28, 16, 4, 5], magN: [33, 16, 4, 2],
  grip: [38, 16, 3, 6], tube: [42, 16, 7, 2], cam: [50, 16, 3, 3],
  limb: [54, 16, 9, 2], bolt: [0, 22, 14, 1], stock: [16, 22, 4, 3],
  receiverTop: [21, 22, 4, 11], glassFx: [52, 20, 3, 2]
};

var GROUPS = {};
function bone(name, origin, parent) {
  var g = new Group({ name: name, origin: origin });
  g.init();
  var p = (parent && GROUPS[parent]) ? GROUPS[parent] : null;
  if (p) g.addTo(p);
  GROUPS[name] = g;
  return g;
}
bone('body', [0, 0, 0], 'root');
bone('scope', [0, 5.5, -3], 'body');
bone('buttstock', [0, 1.0, 8], 'body');
bone('grip', [0, -1.5, 4.6], 'body');
bone('trigger', [0, -1.5, 2.4], 'body');
bone('mag', [0, 5.0, 3.9], 'body');
bone('limb_l', [2.0, 4.25, -8.0], 'body');
bone('limb_r', [-2.0, 4.25, -8.0], 'body');
bone('string_l', [11.4, 4.25, -6.4], 'limb_l');
bone('string_r', [-11.4, 4.25, -6.4], 'limb_r');
bone('bolt', [0, 4.25, -4], 'body');

var CUBES = [
  ['receiver', 'body', [-2, -1.5, -3], [2, 3.5, 8], 'body_main', { east: 'panel', west: 'panel', up: 'receiverTop' }],
  ['riser', 'body', [-2.4, -0.5, -8.2], [2.4, 4.2, -3.0], 'body_main', { east: 'riser', west: 'riser', north: 'riserN' }],
  ['rail', 'body', [-1.2, 3.5, -10], [1.2, 4.0, 1.4], 'metal', { up: 'railTop' }],
  ['scope_mount_fl', 'body', [-1.5, 4.0, -6.6], [-1.0, 5.0, -5.8], 'metal', null],
  ['scope_mount_fr', 'body', [1.0, 4.0, -6.6], [1.5, 5.0, -5.8], 'metal', null],
  ['scope_mount_bl', 'body', [-1.5, 4.0, 0.4], [-1.0, 5.0, 1.2], 'metal', null],
  ['scope_mount_br', 'body', [1.0, 4.0, 0.4], [1.5, 5.0, 1.2], 'metal', null],
  ['magwell', 'body', [-1.6, 3.5, 1.6], [1.6, 5.0, 6.2], 'body_dark', null],
  ['guard_front', 'body', [-1.0, -3.6, 1.2], [1.0, -2.6, 1.8], 'body_dark', null],
  ['guard_bottom', 'body', [-1.0, -3.6, 1.2], [1.0, -2.6, 3.8], 'body_dark', null],

  ['scope_tube', 'scope', [-1.5, 4.8, -7.6], [1.5, 6.4, -0.6], 'scope_body', { east: 'tube', west: 'tube' }],
  ['scope_obj', 'scope', [-1.9, 4.5, -8.6], [1.9, 6.7, -7.6], 'metal', null],
  ['scope_glass', 'scope', [-1.6, 4.7, -8.9], [1.6, 6.5, -8.6], 'glass', { north: 'glassFx' }],
  ['scope_eye', 'scope', [-1.8, 4.6, -0.7], [1.8, 6.6, 0.0], 'metal', null],
  ['scope_turret_v', 'scope', [-0.6, 6.4, -5.2], [0.6, 7.3, -4.2], 'metal', null],
  ['scope_turret_h', 'scope', [1.5, 5.2, -5.2], [2.2, 6.0, -4.2], 'metal', null],

  ['stock_top', 'buttstock', [-1.2, 1.0, 8.0], [1.2, 3.6, 11.2], 'body_main', { east: 'stock', west: 'stock' }],
  ['stock_bot', 'buttstock', [-1.0, -1.2, 8.0], [1.0, 1.2, 10.6], 'body_dark', null],
  ['buttpad', 'buttstock', [-1.4, -1.4, 11.2], [1.4, 4.2, 12.0], 'rubber', null],

  ['grip_body', 'grip', [-1.3, -6.2, 3.4], [1.3, -1.0, 5.8], 'rubber', { east: 'grip', west: 'grip' }],
  ['grip_base', 'grip', [-1.5, -6.6, 3.2], [1.5, -5.8, 6.0], 'rubber', null],

  ['trigger_blade', 'trigger', [-0.35, -3.2, 2.1], [0.35, -1.2, 2.7], 'metal', null],

  ['mag_body', 'mag', [-1.3, 5.0, 1.9], [1.3, 9.4, 5.9], 'body_dark', { east: 'mag', west: 'mag', north: 'magN' }],
  ['mag_floor', 'mag', [-1.45, 9.4, 1.8], [1.45, 10.0, 6.0], 'metal', null],

  ['limb_l_arm', 'limb_l', [2.0, 3.6, -8.6], [11.0, 4.9, -7.4], 'limb', { north: 'limb', south: 'limb' }],
  ['limb_l_mid', 'limb_l', [7.6, 3.5, -9.0], [10.2, 5.0, -7.0], 'limb_hi', null],
  ['limb_l_cam', 'limb_l', [10.4, 3.0, -9.6], [12.4, 5.5, -6.4], 'cam', { east: 'cam', west: 'cam' }],

  ['limb_r_arm', 'limb_r', [-11.0, 3.6, -8.6], [-2.0, 4.9, -7.4], 'limb', { north: 'limb', south: 'limb' }],
  ['limb_r_mid', 'limb_r', [-10.2, 3.5, -9.0], [-7.6, 5.0, -7.0], 'limb_hi', null],
  ['limb_r_cam', 'limb_r', [-12.4, 3.0, -9.6], [-10.4, 5.5, -6.4], 'cam', { east: 'cam', west: 'cam' }],

  ['string_l', 'string_l', [0, 4.05, -6.6], [11.4, 4.45, -6.2], 'string', null],
  ['string_r', 'string_r', [-11.4, 4.05, -6.6], [0, 4.45, -6.2], 'string', null],

  ['bolt_shaft', 'bolt', [-0.3, 4.0, -11.6], [0.3, 4.5, 2.0], 'bolt', { east: 'bolt', west: 'bolt' }],
  ['bolt_head', 'bolt', [-0.5, 3.9, -13.4], [0.5, 4.6, -11.6], 'steel', null],
  ['bolt_fletch_l', 'bolt', [-1.2, 3.9, 0.4], [0.0, 4.6, 2.0], 'bolt', null],
  ['bolt_fletch_r', 'bolt', [0.0, 3.9, 0.4], [1.2, 4.6, 2.0], 'bolt', null]
];

var FACES = ['north', 'south', 'east', 'west', 'up', 'down'];
var i, c;
for (i = 0; i < CUBES.length; i++) {
  var spec = CUBES[i];
  c = new Cube({ name: spec[0], from: spec[2], to: spec[3], box_uv: false, autouv: 0, texture: 0 });
  c.addTo(GROUPS[spec[1]]);
  c.init();
  c.box_uv = false;
  var mat = MAT[spec[4]];
  var uvs = {};
  FACES.forEach(function (f) {
    var r = (spec[5] && spec[5][f] && FACE[spec[5][f]]) || mat;
    uvs[f] = { uv: [r[0], r[1]], uv_size: [r[2], r[3]] };
  });
  c.uv = uvs;
}

Canvas.updateAll();
if (typeof updateUVEditor === 'function') updateUVEditor();

return JSON.stringify({
  cubes: Cube.all.length,
  groups: Group.all.map(function (g) { return g.name + '[' + (g.parent ? g.parent.name : '-') + ']'; }),
  tex: Texture.all.map(function (t) { return t.name + ' ' + t.canvas.width + 'x' + t.canvas.height + ' uv ' + t.getUVWidth() + 'x' + t.getUVHeight(); }),
  res: [Project.texture_width, Project.texture_height]
}, null, 1);
})();
