workspace.windowAdded.connect(function (w) {
    if (!w.normalWindow) return;
    var a = workspace.clientArea(KWin.MaximizeArea, w);
    var width = Math.round(a.width * 0.82);
    var height = Math.round(a.height * 0.82);
    w.frameGeometry = {
        x: a.x + Math.round((a.width - width) / 2),
        y: a.y + Math.round((a.height - height) / 2),
        width: width,
        height: height
    };
});
