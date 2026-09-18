(function () {

  var RES = 64;
  Project.texture_width = RES;
  Project.texture_height = RES;
  Project.box_uv = false;
  Project.geckolib_modid = 'hexalunar_calamity';

  var MAT = {
    body_main: [0, 0], body_hi: [1, 0], body_dark: [2, 0], metal: [3, 0],
    rubber: [4, 0], string: [5, 0], glass: [6, 0], steel: [7, 0],
    limb: [0, 1], cam: [1, 1], limb_hi: [2, 1], accent: [3, 1],
    scope_body: [4, 1], bolt_wood: [5, 1], glass_dark: [6, 1], white: [7, 1]
  };

  var PAT = {
    recvSide: [0, 16, 8, 4], recvTop: [9, 16, 4, 8], midSide: [14, 16, 7, 4],
    rivSide: [22, 16, 5, 5], magSide: [28, 16, 4, 6], gripSide: [33, 16, 3, 5],
    scopeSide: [37, 16, 7, 2], scopeFront: [45, 16, 4, 3], camSide: [50, 16, 3, 3],
    buttSide: [54, 16, 6, 5], railTop: [0, 32, 2, 14], limbTop: [3, 32, 6, 2],
    boltSide: [10, 32, 8, 1], riserSide: [19, 32, 2, 5], misc: [22, 32, 4, 4]
  };

  function matUV(m) {
    var c = MAT[m] || MAT.body_main;
    return { uv: [c[0] * 8 + 3, c[1] * 8 + 3], uv_size: [1, 1] };
  }
  function patUV(p) {
    var r = PAT[p];
    return { uv: [r[0], r[1]], uv_size: [r[2], r[3]] };
  }

  var FACES = ['north', 'south', 'east', 'west', 'up', 'down'];
  var GN = {};
  var CUBES = [];

  function bone(name, parent, pivot) {
    var g = new Group({ name: name, origin: pivot, parent: parent || null });
    g.init();
    g.addTo(parent || 'root');
    GN[name] = g;
    return g;
  }

  function mk(boneName, name, from, to, mat, fx, rot, pivot) {
    var c = new Cube({ name: name, from: from, to: to, box_uv: false, autouv: 0 });
    c.init();
    c.addTo(GN[boneName]);
    c.box_uv = false;
    var uv = {};
    for (var i = 0; i < FACES.length; i++) {
      var f = FACES[i];
      uv[f] = (fx && fx[f]) ? patUV(fx[f]) : matUV(mat);
    }
    c.uv = uv;
    if (rot) { c.rotation = rot; c.origin = pivot || [0, 0, 0]; }
    CUBES.push({ bone: boneName, name: name });
    return c;
  }

  function mirX(spec) {
    return {
      from: [-spec[1][0], spec[0][1], spec[0][2]],
      to: [-spec[0][0], spec[1][1], spec[1][2]]
    };
  }

  bone('root', null, [0, 0, 0]);
  bone('body', GN.root, [0, 0, 0]);
  bone('scope', GN.body, [0, 5.4, -2.0]);
  bone('limb_l', GN.body, [1.8, 3.85, -8.4]);
  bone('limb_r', GN.body, [-1.8, 3.85, -8.4]);
  bone('string_l', GN.limb_l, [10.5, 3.85, -7.2]);
  bone('string_r', GN.limb_r, [-10.5, 3.85, -7.2]);
  bone('mag', GN.body, [0, 4.8, 2.5]);
  bone('bolt', GN.body, [0, 3.85, 0]);
  bone('trigger', GN.body, [0, -1.0, 2.0]);

  mk('body', 'receiver_main', [-1.6, -1.0, -1.0], [1.6, 3.0, 6.4], 'body_main',
    { east: 'recvSide', west: 'recvSide', up: 'recvTop' });
  mk('body', 'receiver_lower', [-1.4, -1.8, 0.4], [1.4, -1.0, 5.2], 'body_dark');
  mk('body', 'mid_body', [-1.5, -1.0, -7.6], [1.5, 2.6, -1.0], 'body_main',
    { east: 'midSide', west: 'midSide' });
  mk('body', 'riser', [-2.4, -1.4, -9.6], [2.4, 3.4, -7.6], 'body_main',
    { east: 'riserSide', west: 'riserSide', north: 'rivSide' });
  mk('body', 'rail', [-1.0, 3.0, -7.4], [1.0, 3.6, 6.0], 'metal', { up: 'railTop' });
  mk('body', 'butt', [-1.4, -1.0, 6.4], [1.4, 3.6, 12.0], 'body_main',
    { east: 'buttSide', west: 'buttSide' });
  mk('body', 'buttpad', [-1.5, -1.4, 12.0], [1.5, 4.0, 12.8], 'rubber');
  mk('body', 'grip', [-1.2, -5.6, 3.2], [1.2, -1.0, 5.4], 'rubber',
    { east: 'gripSide', west: 'gripSide' }, [10, 0, 0], [0, -1.0, 4.3]);
  mk('body', 'guard_bottom', [-1.0, -3.2, 1.7], [1.0, -2.7, 4.2], 'body_dark');
  mk('body', 'guard_front', [-1.0, -2.7, 1.7], [1.0, -1.0, 2.3], 'body_dark');
  mk('body', 'magwell', [-1.45, 3.6, 2.2], [1.45, 4.8, 6.0], 'body_hi');
  mk('body', 'front_sight', [-0.3, 3.6, -7.0], [0.3, 4.5, -6.5], 'metal');
  mk('body', 'mount_f_l', [-1.35, 3.6, -4.6], [-0.9, 4.8, -3.8], 'metal');
  mk('body', 'mount_f_r', [0.9, 3.6, -4.6], [1.35, 4.8, -3.8], 'metal');
  mk('body', 'mount_r_l', [-1.35, 3.6, 0.2], [-0.9, 4.8, 1.0], 'metal');
  mk('body', 'mount_r_r', [0.9, 3.6, 0.2], [1.35, 4.8, 1.0], 'metal');
  mk('body', 'sling_loop', [-1.9, -0.8, 5.4], [-1.5, 0.0, 6.0], 'metal');

  mk('scope', 'scope_tube', [-1.4, 4.7, -5.4], [1.4, 6.1, 1.6], 'scope_body',
    { east: 'scopeSide', west: 'scopeSide' });
  mk('scope', 'scope_objective', [-1.8, 4.3, -6.2], [1.8, 6.5, -5.4], 'metal',
    { north: 'scopeFront' });
  mk('scope', 'scope_ocular', [-1.7, 4.4, 1.6], [1.7, 6.4, 2.4], 'metal');
  mk('scope', 'scope_turret_up', [-0.6, 6.1, -2.6], [0.6, 6.9, -1.6], 'metal');
  mk('scope', 'scope_turret_side', [1.4, 5.0, -2.6], [2.0, 5.8, -1.6], 'metal');

  mk('limb_l', 'l_limb_base', [1.8, 3.15, -9.1], [4.2, 4.55, -7.7], 'limb');
  mk('limb_l', 'l_limb_arm', [4.2, 3.35, -8.95], [10.0, 4.35, -7.85], 'limb_hi',
    { up: 'limbTop', down: 'limbTop' });
  mk('limb_l', 'l_limb_tip', [9.6, 3.35, -8.9], [10.6, 4.35, -7.9], 'limb');
  mk('limb_l', 'l_cam', [9.4, 2.6, -9.5], [11.6, 5.1, -7.2], 'cam',
    { east: 'camSide' });

  var rspec = [
    ['r_limb_base', [1.8, 3.15, -9.1], [4.2, 4.55, -7.7], 'limb', null],
    ['r_limb_arm', [4.2, 3.35, -8.95], [10.0, 4.35, -7.85], 'limb_hi', { up: 'limbTop', down: 'limbTop' }],
    ['r_limb_tip', [9.6, 3.35, -8.9], [10.6, 4.35, -7.9], 'limb', null],
    ['r_cam', [9.4, 2.6, -9.5], [11.6, 5.1, -7.2], 'cam', { west: 'camSide' }]
  ];
  for (var ri = 0; ri < rspec.length; ri++) {
    var s = rspec[ri];
    var m = mirX([s[1], s[2]]);
    mk('limb_r', s[0], m.from, m.to, s[3], s[4]);
  }

  mk('string_l', 'string_left', [0, 3.65, -7.42], [10.5, 4.05, -6.98], 'string');
  mk('string_r', 'string_right', [-10.5, 3.65, -7.42], [0, 4.05, -6.98], 'string');

  mk('mag', 'mag_body1', [-1.2, 4.8, 2.5], [1.2, 6.6, 5.7], 'metal',
    { east: 'magSide', west: 'magSide' });
  mk('mag', 'mag_body2', [-1.2, 6.6, 2.7], [1.2, 8.4, 5.9], 'metal');
  mk('mag', 'mag_body3', [-1.2, 8.4, 3.0], [1.2, 9.6, 6.2], 'metal');
  mk('mag', 'mag_floor', [-1.35, 9.6, 2.8], [1.35, 10.2, 6.4], 'body_dark');

  mk('bolt', 'bolt_shaft', [-0.25, 3.65, -7.6], [0.25, 4.05, 0.6], 'bolt_wood',
    { east: 'boltSide', west: 'boltSide' });
  mk('bolt', 'bolt_nock', [-0.45, 3.6, 0.6], [0.45, 4.1, 1.2], 'accent');
  mk('bolt', 'bolt_head', [-0.5, 3.5, -8.6], [0.5, 4.2, -7.6], 'steel');
  mk('bolt', 'bolt_fletch', [-0.9, 3.4, -0.6], [0.9, 4.3, 0.4], 'accent');

  mk('trigger', 'trigger_plate', [-0.3, -2.6, 1.9], [0.3, -0.6, 2.5], 'metal');

  Canvas.updateAll();

  return JSON.stringify({
    groups: Group.all.map(function (g) { return g.name + '@' + (g.parent ? g.parent.name : '-'); }),
    cubes: Cube.all.length,
    bones: Object.keys(GN).length
  }, null, 1);
})();
