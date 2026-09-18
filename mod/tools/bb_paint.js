(function () {

  var RES = 64;
  var removed = 0;
  Texture.all.slice().forEach(function (t) {
    if (typeof t.remove === 'function') { t.remove(false); removed++; }
  });
  var tex = new Texture({ name: 'crossbow_geo', width: RES, height: RES, particle: true });
  tex.add();
  var ctx = tex.ctx;

  function rgb(hex) {
    hex = hex.replace('#', '');
    return [parseInt(hex.substr(0, 2), 16), parseInt(hex.substr(2, 2), 16), parseInt(hex.substr(4, 2), 16)];
  }
  function fill(x, y, w, h, hex) {
    var c = rgb(hex);
    ctx.fillStyle = 'rgb(' + c[0] + ',' + c[1] + ',' + c[2] + ')';
    ctx.fillRect(x, y, w, h);
  }
  function px(x, y, hex) { fill(x, y, 1, 1, hex); }
  function row(x, y, w, hex) { fill(x, y, w, 1, hex); }
  function col(x, y, h, hex) { fill(x, y, 1, h, hex); }

  fill(0, 0, RES, RES, '#101014');

  var SW = [
    [0, 0, '#17171A'], [8, 0, '#26262C'], [16, 0, '#0C0C0F'], [24, 0, '#3B3B43'],
    [32, 0, '#0F0F12'], [40, 0, '#C9C2AE'], [48, 0, '#1D4A63'], [56, 0, '#7C7C86'],
    [0, 8, '#101014'], [8, 8, '#2A2A31'], [16, 8, '#1C1C22'], [24, 8, '#6E6E78'],
    [32, 8, '#1A1A1F'], [40, 8, '#2E2E34'], [48, 8, '#0B2A3A'], [56, 8, '#D8D8DC']
  ];
  for (var i = 0; i < SW.length; i++) { fill(SW[i][0], SW[i][1], 8, 8, SW[i][2]); }

  var P = {
    recvSide: [0, 16, 8, 4], recvTop: [9, 16, 4, 8], midSide: [14, 16, 7, 4],
    rivSide: [22, 16, 5, 5], magSide: [28, 16, 4, 6], gripSide: [33, 16, 3, 5],
    scopeSide: [37, 16, 7, 2], scopeFront: [45, 16, 4, 3], camSide: [50, 16, 3, 3],
    buttSide: [54, 16, 6, 5], railTop: [0, 32, 2, 14], limbTop: [3, 32, 6, 2],
    boltSide: [10, 32, 8, 1], riserSide: [19, 32, 2, 5], misc: [22, 32, 4, 4]
  };

  var r = P.recvSide;
  fill(r[0], r[1], r[2], r[3], '#17171A');
  row(r[0], r[1], r[2], '#22222A');
  row(r[0], r[1] + 3, r[2], '#0A0A0C');
  fill(r[0] + 2, r[1] + 1, 4, 1, '#0A0A0C');
  fill(r[0] + 5, r[1] + 2, 3, 1, '#2E2E36');
  px(r[0], r[1] + 1, '#5A5A64');
  px(r[0] + 7, r[1] + 1, '#5A5A64');
  px(r[0], r[1] + 2, '#5A5A64');
  px(r[0] + 7, r[1] + 2, '#5A5A64');

  r = P.recvTop;
  fill(r[0], r[1], r[2], r[3], '#1C1C22');
  col(r[0], r[1], r[3], '#26262C');
  col(r[0] + 3, r[1], r[3], '#26262C');
  col(r[0] + 1, r[1], r[3], '#0C0C0F');
  col(r[0] + 2, r[1], r[3], '#0C0C0F');

  r = P.midSide;
  fill(r[0], r[1], r[2], r[3], '#17171A');
  row(r[0], r[1], r[2], '#22222A');
  row(r[0], r[1] + 3, r[2], '#0A0A0C');
  col(r[0] + 1, r[1] + 1, 2, '#0A0A0C');
  col(r[0] + 3, r[1] + 1, 2, '#0A0A0C');
  col(r[0] + 5, r[1] + 1, 2, '#0A0A0C');
  px(r[0] + 6, r[1] + 1, '#5A5A64');

  r = P.rivSide;
  fill(r[0], r[1], r[2], r[3], '#1A1A1F');
  fill(r[0] + 1, r[1] + 1, 3, 3, '#101014');
  px(r[0], r[1], '#5A5A64');
  px(r[0] + 4, r[1], '#5A5A64');
  px(r[0], r[1] + 4, '#5A5A64');
  px(r[0] + 4, r[1] + 4, '#5A5A64');
  row(r[0], r[1] + 2, r[2], '#22222A');

  r = P.magSide;
  fill(r[0], r[1], r[2], r[3], '#2F2F36');
  col(r[0], r[1], r[3], '#3B3B43');
  col(r[0] + 3, r[1], r[3], '#232329');
  row(r[0], r[1] + 1, r[2], '#43434C');
  row(r[0], r[1] + 3, r[2], '#43434C');
  row(r[0], r[1] + 5, r[2], '#0C0C0F');
  px(r[0] + 1, r[1] + 2, '#54545E');

  r = P.gripSide;
  fill(r[0], r[1], r[2], r[3], '#0F0F12');
  px(r[0] + 1, r[1], '#1A1A20');
  px(r[0], r[1] + 1, '#1A1A20');
  px(r[0] + 2, r[1] + 1, '#1A1A20');
  px(r[0] + 1, r[1] + 2, '#1A1A20');
  px(r[0], r[1] + 3, '#1A1A20');
  px(r[0] + 2, r[1] + 3, '#1A1A20');
  px(r[0] + 1, r[1] + 4, '#1A1A20');
  row(r[0], r[1], r[2], '#17171A');

  r = P.scopeSide;
  fill(r[0], r[1], r[2], r[3], '#1A1A1F');
  row(r[0], r[1], r[2], '#2A2A31');
  row(r[0], r[1] + 1, r[2], '#0C0C0F');
  col(r[0] + 1, r[1], r[3], '#26262C');
  col(r[0] + 5, r[1], r[3], '#26262C');

  r = P.scopeFront;
  fill(r[0], r[1], r[2], r[3], '#0C0C0F');
  fill(r[0] + 1, r[1] + 1, 2, 1, '#3E8FBE');
  px(r[0] + 1, r[1], '#1A1A1F');
  px(r[0] + 2, r[1], '#1A1A1F');
  px(r[0], r[1] + 1, '#1A1A1F');
  px(r[0] + 3, r[1] + 1, '#1A1A1F');
  fill(r[0], r[1] + 2, 4, 1, '#17171A');
  px(r[0] + 2, r[1] + 2, '#2E5C7A');

  r = P.camSide;
  fill(r[0], r[1], r[2], r[3], '#2A2A31');
  px(r[0] + 1, r[1] + 1, '#6E6E78');
  px(r[0] + 1, r[1], '#3A3A44');
  px(r[0] + 1, r[1] + 2, '#3A3A44');
  px(r[0], r[1] + 1, '#3A3A44');
  px(r[0] + 2, r[1] + 1, '#3A3A44');
  px(r[0], r[1], '#16161A');
  px(r[0] + 2, r[1], '#16161A');
  px(r[0], r[1] + 2, '#16161A');
  px(r[0] + 2, r[1] + 2, '#16161A');

  r = P.buttSide;
  fill(r[0], r[1], r[2], r[3], '#17171A');
  row(r[0], r[1], r[2], '#22222A');
  row(r[0], r[1] + 4, r[2], '#0A0A0C');
  fill(r[0] + 2, r[1] + 3, 2, 1, '#0A0A0C');
  px(r[0], r[1] + 1, '#2E2E36');
  px(r[0] + 5, r[1] + 2, '#2E2E36');
  col(r[0] + 5, r[1], r[3], '#121216');

  r = P.railTop;
  fill(r[0], r[1], r[2], r[3], '#3B3B43');
  for (var v = 0; v < 14; v += 2) { row(r[0], r[1] + v, r[2], '#202027'); }
  col(r[0], r[1], r[3], '#4A4A54');
  col(r[0] + 1, r[1], r[3], '#33333B');

  r = P.limbTop;
  fill(r[0], r[1], r[2], r[3], '#1C1C22');
  row(r[0], r[1], r[2], '#2A2A31');
  row(r[0], r[1] + 1, r[2], '#0C0C0F');
  col(r[0] + 5, r[1], r[3], '#101014');
  px(r[0] + 4, r[1], '#33333B');

  r = P.boltSide;
  fill(r[0], r[1], r[2], r[3], '#2E2E34');
  fill(r[0], r[1], 5, 1, '#3E3E46');
  px(r[0] + 6, r[1], '#6E6E78');

  r = P.riserSide;
  fill(r[0], r[1], r[2], r[3], '#17171A');
  col(r[0], r[1], r[3], '#22222A');
  px(r[0] + 1, r[1] + 1, '#5A5A64');
  px(r[0] + 1, r[1] + 3, '#5A5A64');
  px(r[0] + 1, r[1] + 4, '#0A0A0C');

  r = P.misc;
  fill(r[0], r[1], r[2], r[3], '#17171A');
  fill(r[0] + 1, r[1] + 1, 2, 2, '#2E2E36');
  px(r[0] + 1, r[1] + 1, '#C9C2AE');

  Cube.all.forEach(function (c) { c.texture = 0; });
  try {
    tex.setAsDefaultTexture();
    Cube.all.forEach(function (c) { c.texture = 0; });
  } catch (e) { }
  try { tex.updateChangesAfterEdit(true); } catch (e) { }
  Canvas.updateAll();

  return JSON.stringify({
    removed: removed,
    textures: Texture.all.map(function (t) { return t.name + ' ' + t.width + 'x' + t.height + (t.particle ? ' [particle]' : ''); }),
    cubes: Cube.all.length,
    cube_tex: Cube.all.length ? Cube.all[0].texture : null
  }, null, 1);
})();
