(function () {
  var list = Texture.all.map(function (t) {
    return {
      name: t.name, w: t.width, h: t.height,
      cw: t.canvas ? t.canvas.width : null, ch: t.canvas ? t.canvas.height : null,
      particle: !!t.particle, uv: [t.getUVWidth(), t.getUVHeight()]
    };
  });
  return JSON.stringify({
    project_res: [Project.texture_width, Project.texture_height],
    single_texture: Project.format.single_texture,
    count: Texture.all.length,
    list: list,
    def_is_first: Texture.all.length ? (Texture.getDefault() === Texture.all[0]) : null,
    def_size: Texture.all.length ? Texture.getDefault().width : null
  }, null, 1);
})();
