(function () {
  Texture.all.slice().forEach(function (t) { if (typeof t.remove === 'function') { t.remove(false); } });
  var t = Texture.fromDataURL('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAB/klEQVR42u2ZP2vCQBiHna2gSFEIloqC0FAixeKg4GLpIB2dpHRpZ+dSnLv2m/QjdOjWb+DQ75LyS3lLcrm8MSrSmN/wcN6F+/fkTby7lJpNx9fo9S5VKpWqyng8ValW6ypfn+8qZ7NHldXqVaVEARRAARRAARRQYAG12qmv4bpXKq1WR2W5fFZxnHMVz7tWOXFHKuv1twoFUAAFUAAFUECRBXQ6rq8BCeEFD36jLK3OYvEUmQjyKMfip98fBnS7F0EZFlyO0w5SkY5+wqIlj+sYh7SL3yhrNBx/NLoJ0qTx1euN2A0uYWDouFyuRECZDNomQOqYqdTB4MIdSX46vYvwe60drPqQygTNVabkpa3J20eAtIvJI6KQIu95w9iqVhUQBpXBNgLkLiZFBiJgPn+IRIBMHmnaIyl9B+O8f/nrz4wA27LeKsC88yZJAtLq7BIB+0AmHY5oq4BNGrMJSCPLOyBrBGyC7cYcVEAS5m5xXxPeloML+G9QwDFNhgIogAIogAIogAKyCZjN5v5gMLYefkg5mExuY+BAAltQpLIDlN2ZuRPLhQDbl50sjUGAbHowaXy5kX15LgTsihkBcq5QKAHhCMjdI7APAXIgksuXYOH/BSiAAiiAAiiAAiiA22EKoAAKoAAKoAAKoAAKoAAKoAAKoAAKoAAKOGJ+AOq7yzugaveaAAAAAElFTkSuQmCC', 'crossbow_geo', true);
  try { t.setAsDefaultTexture(); } catch (e) { }
  Cube.all.forEach(function (c) { c.texture = 0; });
  Canvas.updateAll();
  return JSON.stringify({ tex: Texture.all.map(function (x) { return x.name + ' ' + x.width + 'x' + x.height; }), cube_tex: Cube.all.length ? Cube.all[0].texture : null });
})();
