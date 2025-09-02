if (!window.dash_clientside) { window.dash_clientside = {}; }
if (!window.dash_clientside.clientside) { window.dash_clientside.clientside = {}; }
window.dash_clientside.clientside.render_niivue_with_settings = function(niivue_options_json, volume_list_data_json) {
    // Parse the JSON strings
    const niivue_options = JSON.parse(niivue_options_json);
    const volume_list_data = JSON.parse(volume_list_data_json);

    // Clear previous viewer if any
    const container = document.getElementById('niivue-canvas'); // Changed from niivue-container
    if (container) {
        container.innerHTML = '';
    }

    const nv = new niivue.Niivue(niivue_options);
    nv.attachTo('niivue-canvas'); // Changed from niivue-container
    
    nv.loadVolumes(volume_list_data);
    return;
};
