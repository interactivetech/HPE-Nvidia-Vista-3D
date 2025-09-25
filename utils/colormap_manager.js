/**
 * Colormap Manager for Vista3D
 * Handles loading and managing different colormap sets
 */
class ColormapManager {
    constructor() {
        this.colormapSets = {};
        this.defaultSet = 'basic_medical';
        this.loadColormapSets();
    }

    async loadColormapSets() {
        const sets = ['basic_medical', 'scientific', 'medical_specific', 'ct_brain', 'linspecer', 'vista3d_voxels'];
        
        // Get the image server URL from the global variable or use default
        const imageServerUrl = window.IMAGE_SERVER_URL || 'http://localhost:8888';
        
        for (const setName of sets) {
            try {
                const response = await fetch(`${imageServerUrl}/assets/colormaps/${setName}.json`);
                if (response.ok) {
                    const text = await response.text();
                    // Check if the response is HTML (error page) instead of JSON
                    if (text.trim().startsWith('<!DOCTYPE html>') || text.trim().startsWith('<html')) {
                        console.warn(`Colormap set ${setName} returned HTML instead of JSON - server may be misconfigured`);
                        continue;
                    }
                    
                    try {
                        this.colormapSets[setName] = JSON.parse(text);
                        console.log(`Loaded colormap set: ${setName}`);
                    } catch (parseError) {
                        console.warn(`Error parsing JSON for colormap set ${setName}:`, parseError);
                        console.warn(`Response text preview:`, text.substring(0, 200));
                    }
                } else {
                    console.warn(`Could not load colormap set: ${setName} (HTTP ${response.status})`);
                }
            } catch (error) {
                console.warn(`Error loading colormap set ${setName}:`, error);
            }
        }
    }

    getColormaps(setName = null) {
        const set = setName || this.defaultSet;
        return this.colormapSets[set]?.colormaps || [];
    }

    getAllColormaps() {
        const all = [];
        Object.values(this.colormapSets).forEach(set => {
            if (set.colormaps) {
                all.push(...set.colormaps);
            }
        });
        return [...new Set(all)]; // Remove duplicates
    }

    getAvailableSets() {
        return Object.keys(this.colormapSets);
    }

    getSetInfo(setName) {
        return this.colormapSets[setName] || null;
    }
}

// Make it globally available
window.ColormapManager = ColormapManager;
