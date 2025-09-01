if (!window.dash_clientside) { window.dash_clientside = {}; }
if (!window.dash_clientside.clientside) { window.dash_clientside.clientside = {}; }
window.dash_clientside.clientside.render_niivue_with_settings = function(file_urls, color_map, show_crosshair, back_color_str) {
    if (!file_urls || file_urls.length === 0) {
        const container = document.getElementById('niivue-container');
        if (container) {
            container.innerHTML = '';
        }
        return;
    }

    // Clear previous viewer if any
    const container = document.getElementById('niivue-container');
    if (container) {
        container.innerHTML = '';
    }

    const back_color = back_color_str.split(',').map(Number);

    const nv = new niivue.Niivue({
        show3Dcrosshair: show_crosshair.includes('show'),
        backColor: back_color,
    });
    nv.attachTo('niivue-container');
    
    const volumeList = [{
        url: file_urls[0], // file_urls is a list with one element
        colormap: color_map,
    }];
    
    nv.loadVolumes(volumeList);
    return;
};
