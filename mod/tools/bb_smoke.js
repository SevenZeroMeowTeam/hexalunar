(function () {
var out = {};
var tex = new Texture({ name: 'crossbow', width: 64, height: 64, particle: false });
tex.add();
out.tex_ok = tex.name + ' ' + tex.width + 'x' + tex.height;
out.has_ctx = !!(tex.ctx);
out.has_canvas = !!(tex.canvas);
try {
  var img = tex.ctx.createImageData(64, 64);
  for (var i = 0; i < img.data.length; i += 4) {
    img.data[i] = 20; img.data[i + 1] = 20; img.data[i + 2] = 26; img.data[i + 3] = 255;
  }
  tex.ctx.putImageData(img, 0, 0);
  tex.update ? tex.update() : null;
  out.paint = 'ok';
} catch (e) { out.paint = 'ERR ' + e.message; }

var root = new Group({ name: 'root', origin: [0, 0, 0] });
root.init();
root.addTo('root');
out.group_ok = root.name + ' uuid=' + (root.uuid ? 'yes' : 'no');

var child = new Group({ name: 'body', origin: [0, 0, 0], parent: root });
child.init();
child.addTo(root);
out.child_parent = child.parent ? child.parent.name : 'null';

var c = new Cube({ name: 'recv', from: [-1, 0, -1], to: [1, 2, 4], box_uv: false, autouv: 0 });
c.init();
c.addTo(child);
c.box_uv = false;
c.uv = {
  north: { uv: [3, 3], uv_size: [1, 1] },
  south: { uv: [3, 3], uv_size: [1, 1] },
  east: { uv: [3, 3], uv_size: [1, 1] },
  west: { uv: [3, 3], uv_size: [1, 1] },
  up: { uv: [3, 3], uv_size: [1, 1] },
  down: { uv: [3, 3], uv_size: [1, 1] }
};
out.cube_ok = c.name + ' faces=' + Object.keys(c.uv).length;

var c2 = new Cube({ name: 'rot', from: [-1, 0, -1], to: [1, 2, 1], origin: [0, 0, 0], box_uv: false, autouv: 0 });
c2.init();
c2.addTo(child);
c2.rotation = [0, 15, 0];
out.cube_rot = JSON.stringify(c2.rotation);

Canvas.updateAll();
Project.save ? null : null;
out.total_cubes = Cube.all.length;
out.groups = Group.all.map(function (g) { return g.name; });
return JSON.stringify(out, null, 1);
})();
