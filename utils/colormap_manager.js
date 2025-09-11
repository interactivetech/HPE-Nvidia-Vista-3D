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
        const sets = ['basic_medical', 'scientific', 'medical_specific'];
        
        for (const setName of sets) {
            try {
                const response = await fetch(`/assets/colormaps/${setName}.json`);
                if (response.ok) {
                    this.colormapSets[setName] = await response.json();
                    console.log(`Loaded colormap set: ${setName}`);
                } else {
                    console.warn(`Could not load colormap set: ${setName}`);
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
