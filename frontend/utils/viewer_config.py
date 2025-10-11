"""
Viewer Configuration for Vista3D Application
Manages viewer settings, state, and UI configuration.
"""

import streamlit as st
from typing import Dict, Any, Optional, Tuple
from .constants import (
    DEFAULT_VIEWER_SETTINGS, SLICE_TYPE_MAP, WINDOW_PRESETS,
    WINDOW_PRESETS_CT, WINDOW_PRESETS_MRI, get_optimal_window_settings,
    detect_modality_from_data, load_colormaps, VOXEL_MODES, MESSAGES,
    load_3d_render_config
)


class ViewerConfig:
    """
    Manages viewer configuration and state.
    Provides methods for getting and setting viewer settings.
    """

    def __init__(self):
        self._settings = DEFAULT_VIEWER_SETTINGS.copy()
        self._selected_patient: Optional[str] = None
        self._selected_file: Optional[str] = None
        self._voxel_mode: str = "all"
        self._selected_individual_voxels: list = []
        self._selected_effect: Optional[str] = None

    @property
    def settings(self) -> Dict[str, Any]:
        """Get current viewer settings."""
        return self._settings.copy()

    @property
    def selected_patient(self) -> Optional[str]:
        """Get currently selected patient."""
        return self._selected_patient

    @selected_patient.setter
    def selected_patient(self, patient: Optional[str]):
        """Set selected patient."""
        self._selected_patient = patient

    @property
    def selected_file(self) -> Optional[str]:
        """Get currently selected file."""
        return self._selected_file

    @selected_file.setter
    def selected_file(self, file: Optional[str]):
        """Set selected file."""
        self._selected_file = file

    @property
    def voxel_mode(self) -> str:
        """Get current voxel selection mode."""
        return self._voxel_mode

    @voxel_mode.setter
    def voxel_mode(self, mode: str):
        """Set voxel selection mode."""
        self._voxel_mode = mode

    @property
    def selected_individual_voxels(self) -> list:
        """Get selected individual voxels."""
        return self._selected_individual_voxels.copy()

    @selected_individual_voxels.setter
    def selected_individual_voxels(self, voxels: list):
        """Set selected individual voxels."""
        self._selected_individual_voxels = voxels.copy()

    def get_slice_type_index(self) -> int:
        """Get the numeric slice type index for NiiVue."""
        slice_type = self._settings.get('slice_type', 'Multiplanar')
        orientation = self._settings.get('orientation', 'Axial')

        if slice_type == "Single View":
            return SLICE_TYPE_MAP.get(orientation, 3)
        return SLICE_TYPE_MAP.get(slice_type, 3)

    def apply_window_preset(self, preset_name: str):
        """Apply a window preset to the viewer settings."""
        if preset_name in WINDOW_PRESETS:
            center, width = WINDOW_PRESETS[preset_name]
            self._settings['window_center'] = center
            self._settings['window_width'] = width

    def get_window_settings(self) -> Tuple[int, int]:
        """Get current window center and width."""
        return (
            self._settings.get('window_center', 0),
            self._settings.get('window_width', 1000)
        )
    
    def get_dynamic_nifti_opacity(self) -> float:
        """Get CT scan opacity adjusted based on whether voxels are being displayed."""
        base_opacity = self._settings.get('nifti_opacity', 0.5)
        show_voxels = self._settings.get('show_overlay', False)
        
        # If voxels are being displayed, maintain much better background visibility
        if show_voxels:
            return min(base_opacity * 1.2, 0.9)  # Increase to 120% of base opacity, max 0.9 for much better background visibility
        else:
            return base_opacity  # Use full opacity when no voxels

    def apply_optimal_window_settings(self, min_value: float, max_value: float, mean_value: float):
        """Apply optimal window settings based on data characteristics."""
        optimal_center, optimal_width = get_optimal_window_settings(min_value, max_value, mean_value)
        self._settings['window_center'] = optimal_center
        self._settings['window_width'] = optimal_width

    def get_modality_specific_presets(self, min_value: float = None, max_value: float = None, mean_value: float = None):
        """Get window presets appropriate for the detected modality."""
        if min_value is not None and max_value is not None and mean_value is not None:
            modality = detect_modality_from_data(min_value, max_value, mean_value)
            if modality == 'MRI':
                return WINDOW_PRESETS_MRI
        return WINDOW_PRESETS_CT

    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self._settings = DEFAULT_VIEWER_SETTINGS.copy()
        self._voxel_mode = "all"
        self._selected_individual_voxels = []

    def to_session_state(self):
        """Update Streamlit session state with current settings."""
        st.session_state.voxel_mode = self._voxel_mode
        st.session_state.selected_individual_voxels = self._selected_individual_voxels
        # Note: slice_type, orientation, and color_map are now managed by widgets
        # and should not be manually set here to avoid StreamlitAPIException

    def to_session_state_voxels_only(self):
        """Update only voxel-related fields in session state.

        This avoids unintentionally overwriting the user's current
        slice/orientation selections when interacting with voxel UI.
        """
        # Preserve current slice view settings before updating voxel settings
        self._preserve_slice_view_settings()
        
        st.session_state.voxel_mode = self._voxel_mode
        st.session_state.selected_individual_voxels = self._selected_individual_voxels

    def _preserve_slice_view_settings(self):
        """Preserve current slice view settings in session state.
        
        This ensures that when voxel operations occur, the user's
        selected slice view mode (Single View, Multiplanar, 3D Render)
        and orientation are not lost.
        """
        # Only preserve if the settings exist in session state
        if 'slice_type' in st.session_state:
            self._settings['slice_type'] = st.session_state.slice_type
        if 'orientation' in st.session_state:
            self._settings['orientation'] = st.session_state.orientation
        if 'color_map' in st.session_state:
            self._settings['color_map'] = st.session_state.color_map

    def from_session_state(self):
        """Load settings from Streamlit session state."""
        self._voxel_mode = getattr(st.session_state, 'voxel_mode', 'all')
        self._selected_individual_voxels = getattr(st.session_state, 'selected_individual_voxels', [])
        self._settings['slice_type'] = getattr(st.session_state, 'slice_type', 'Multiplanar')
        self._settings['orientation'] = getattr(st.session_state, 'orientation', 'Axial')
        self._settings['color_map'] = getattr(st.session_state, 'color_map', 'niivue-ct_translucent')

    def render_sidebar_settings(self, min_value: float = None, max_value: float = None, mean_value: float = None, has_voxels: bool = False):
        """Render the viewer settings in the sidebar."""
        # Slice type selection
        st.markdown("Select Slice")
        slice_options = ["3D Render", "Multiplanar", "Single View"]
        current_slice = st.selectbox(
            "Slice Type",
            slice_options,
            index=slice_options.index(self._settings['slice_type']) if self._settings['slice_type'] in slice_options else 0,
            label_visibility="collapsed",
            key="slice_type"
        )
        self._settings['slice_type'] = current_slice

        # Orientation for single view
        if current_slice == "Single View":
            orientations = ["Axial", "Coronal", "Sagittal"]
            self._settings['orientation'] = st.selectbox(
                "Orientation",
                orientations,
                index=orientations.index(self._settings.get('orientation', 'Axial')),
                key="orientation"
            )

        # Color Map Selection - moved above NIfTI Image Settings
        st.markdown("Color Map")
        # Load colormaps dynamically to get the updated list
        available_colormaps = load_colormaps()
        # Get current color map index, with fallback to 0 if not found
        current_color_map = self._settings['color_map']
        try:
            color_map_index = available_colormaps.index(current_color_map)
        except ValueError:
            # If current color map is not in the list, use first available (niivue-ct_translucent)
            color_map_index = 0
            self._settings['color_map'] = available_colormaps[0]
        
        selected_color_map = st.selectbox(
            "Select Color Map",
            available_colormaps,
            index=color_map_index,
            label_visibility="collapsed",
            key="color_map"
        )
        self._settings['color_map'] = selected_color_map

        # NIfTI display settings - always show NIfTI
        self._settings['show_nifti'] = True
        
        with st.expander("Image Settings", expanded=False):
            st.info("💡 **Smart Opacity**: CT scan automatically becomes more transparent when voxels are displayed to improve visibility.")
            self._settings['nifti_opacity'] = st.slider(
                "Scan Base Opacity",
                0.0, 1.0,
                self._settings['nifti_opacity'],
                help="Base opacity for CT scan. When voxels are shown, this is automatically reduced to 60% for better background visibility."
            )
            self._settings['nifti_gamma'] = st.slider(
                "Scan Gamma",
                0.1, 3.0,
                self._settings['nifti_gamma'],
                step=0.1,
                key="nifti_gamma"
            )
            self._settings['view_fit_zoom'] = st.slider(
                "View Fit Zoom",
                1.0, 5.0,
                self._settings.get('view_fit_zoom', 3.0),
                step=0.1,
                help="Controls how much of the CT scan is visible. Higher values show more of the scan, lower values zoom in closer."
            )

        # 3D Render Quality Settings
        with st.expander("3D Render Quality", expanded=False):
            # 3D Render Quality Preset
            quality_presets = ["3d_render_ultra", "3d_render_quality", "3d_render_balanced", "3d_render_performance", "3d_render_medical_realistic"]
            preset_labels = ["Ultra Quality", "High Quality", "Balanced", "Performance", "Medical Realistic"]
            
            current_preset = self._settings.get('3d_render_preset', '3d_render_quality')
            try:
                preset_index = quality_presets.index(current_preset)
            except ValueError:
                preset_index = 1  # Default to high quality
            
            selected_preset = st.selectbox(
                "Render Quality Preset",
                preset_labels,
                index=preset_index,
                help="Choose rendering quality preset. Medical Realistic for enhanced anatomical visualization, Ultra for best quality, Performance for speed."
            )
            
            # Map back to preset name
            self._settings['3d_render_preset'] = quality_presets[preset_labels.index(selected_preset)]
            
            # Depth and Transparency Controls
            st.markdown("**Depth & Transparency**")
            
            self._settings['alpha_test'] = st.slider(
                "Alpha Test Threshold",
                0.01, 0.5,
                self._settings.get('alpha_test', 0.1),
                step=0.01,
                help="Lower values show more transparent voxels"
            )
            
            self._settings['transparency_quality'] = st.selectbox(
                "Transparency Quality",
                ["low", "medium", "high", "ultra"],
                index=2,  # Default to high
                help="Quality of transparency rendering"
            )
            
            self._settings['depth_precision'] = st.selectbox(
                "Depth Precision",
                ["low", "medium", "high", "ultra"],
                index=2,  # Default to high
                help="Precision of depth testing"
            )
            
            # Lighting Controls
            st.markdown("**Lighting**")
            
            self._settings['ambient_light'] = st.slider(
                "Ambient Light",
                0.0, 1.0,
                self._settings.get('ambient_light', 0.2),
                step=0.05,
                help="Base lighting level (0.0 = dark, 1.0 = bright)"
            )
            
            self._settings['directional_light'] = st.slider(
                "Directional Light",
                0.0, 1.0,
                self._settings.get('directional_light', 0.8),
                step=0.05,
                help="Main light source intensity (0.0 = no shadows, 1.0 = strong shadows)"
            )
            
            # Light position controls
            st.markdown("**Light Position**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                self._settings['light_x'] = st.slider(
                    "X", -2.0, 2.0, 
                    self._settings.get('light_x', 1.0), 
                    step=0.1, key="light_x"
                )
            with col2:
                self._settings['light_y'] = st.slider(
                    "Y", -2.0, 2.0, 
                    self._settings.get('light_y', 1.0), 
                    step=0.1, key="light_y"
                )
                with col3:
                    self._settings['light_z'] = st.slider(
                        "Z", -2.0, 2.0, 
                        self._settings.get('light_z', 1.0), 
                        step=0.1, key="light_z"
                    )
            
            # Advanced Shader Effects
            st.markdown("**Advanced Shader Effects**")
            
            # Ambient Occlusion
            self._settings['ambient_occlusion'] = st.checkbox(
                "Ambient Occlusion",
                value=self._settings.get('ambient_occlusion', True),
                help="Adds soft shadows in crevices and corners"
            )
            
            if self._settings['ambient_occlusion']:
                col1, col2 = st.columns(2)
                with col1:
                    self._settings['ao_intensity'] = st.slider(
                        "AO Intensity", 0.0, 1.0,
                        self._settings.get('ao_intensity', 0.8),
                        step=0.1, help="Shadow intensity"
                    )
                with col2:
                    self._settings['ao_radius'] = st.slider(
                        "AO Radius", 0.5, 3.0,
                        self._settings.get('ao_radius', 2.0),
                        step=0.1, help="Shadow radius"
                    )
            
            # Bloom Effect
            self._settings['bloom'] = st.checkbox(
                "Bloom",
                value=self._settings.get('bloom', True),
                help="Adds glow around bright areas"
            )
            
            if self._settings['bloom']:
                col1, col2 = st.columns(2)
                with col1:
                    self._settings['bloom_intensity'] = st.slider(
                        "Bloom Intensity", 0.0, 1.0,
                        self._settings.get('bloom_intensity', 0.3),
                        step=0.05, help="Glow intensity"
                    )
                with col2:
                    self._settings['bloom_threshold'] = st.slider(
                        "Bloom Threshold", 0.0, 1.0,
                        self._settings.get('bloom_threshold', 0.7),
                        step=0.05, help="Brightness threshold for glow"
                    )
            
            # Depth of Field
            self._settings['depth_of_field'] = st.checkbox(
                "Depth of Field",
                value=self._settings.get('depth_of_field', True),
                help="Blurs out-of-focus areas"
            )
            
            if self._settings['depth_of_field']:
                col1, col2 = st.columns(2)
                with col1:
                    self._settings['dof_focus'] = st.slider(
                        "Focus Distance", 0.0, 1.0,
                        self._settings.get('dof_focus', 0.5),
                        step=0.05, help="Focus point"
                    )
                with col2:
                    self._settings['dof_blur'] = st.slider(
                        "Blur Amount", 0.0, 1.0,
                        self._settings.get('dof_blur', 0.2),
                        step=0.05, help="Blur intensity"
                    )
            
            # Vignette
            self._settings['vignette'] = st.checkbox(
                "Vignette",
                value=self._settings.get('vignette', True),
                help="Darkens edges for cinematic effect"
            )
            
            if self._settings['vignette']:
                col1, col2 = st.columns(2)
                with col1:
                    self._settings['vignette_intensity'] = st.slider(
                        "Vignette Intensity", 0.0, 1.0,
                        self._settings.get('vignette_intensity', 0.3),
                        step=0.05, help="Edge darkening amount"
                    )
                with col2:
                    self._settings['vignette_radius'] = st.slider(
                        "Vignette Radius", 0.0, 1.0,
                        self._settings.get('vignette_radius', 0.8),
                        step=0.05, help="Edge effect radius"
                    )

            # Window/Level settings (CT/MRI adaptive)
            st.markdown("**Window/Level Settings**")
            
            # Show modality detection info if available
            if min_value is not None and max_value is not None and mean_value is not None:
                modality = detect_modality_from_data(min_value, max_value, mean_value)
                current_center, current_width = self.get_window_settings()
                optimal_center, optimal_width = get_optimal_window_settings(min_value, max_value, mean_value)
                
                if current_center == optimal_center and current_width == optimal_width:
                    st.success(f"✅ Auto-applied {modality} optimal settings: Center={current_center}, Width={current_width}")
                else:
                    st.info(f"📊 {modality} data detected (range: {min_value:.0f}-{max_value:.0f}, mean: {mean_value:.0f})")
            self._settings['window_center'] = st.slider(
                "Window Center (Level)",
                -2500, 2500,
                self._settings['window_center'],
                key="window_center"
            )
            self._settings['window_width'] = st.slider(
                "Window Width",
                50, 5000,
                self._settings['window_width'],
                key="window_width"
            )

            # Preset windowing options (modality-specific)
            modality_presets = self.get_modality_specific_presets(min_value, max_value, mean_value)
            preset_options = list(modality_presets.keys())
            window_preset = st.selectbox(
                "Window Preset",
                preset_options,
                key="window_preset"
            )

            if window_preset != "Custom":
                self.apply_window_preset(window_preset)

        # Voxel display settings - only show if voxels are available
        if has_voxels:
            self._settings['show_overlay'] = st.checkbox("Show Voxels", value=self._settings['show_overlay'])
        else:
            # If no voxels available, ensure show_overlay is False
            self._settings['show_overlay'] = False
        
        # Show Scan setting removed - CT scan is now always shown with dynamic opacity
        
        # Save settings to session state
        self.to_session_state()

    def render_voxel_image_settings(self):
        """Render the voxel image settings in an expander."""
        if self._settings['show_overlay']:
            with st.expander("Voxel Image Settings", expanded=False):
                self._settings['segment_opacity'] = st.slider(
                    "Voxel Opacity",
                    0.0, 1.0,
                    self._settings['segment_opacity'],
                    key="segment_opacity"
                )
                self._settings['segment_gamma'] = st.slider(
                    "Voxel Gamma",
                    0.1, 3.0,
                    self._settings['segment_gamma'],
                    step=0.1,
                    key="segment_gamma"
                )

    def render_voxel_legend(self):
        """Render the voxel legend in an expander."""
        with st.expander("Voxel Legend", expanded=False):
            try:
                from .config_manager import ConfigManager
                config = ConfigManager()
                for label_info in config.label_colors:
                    label_name = label_info.get("name", "")
                    label_id = label_info.get("id", 0)
                    color_rgb = label_info.get("color", [0, 0, 0])
                    color_hex = f"#{color_rgb[0]:02x}{color_rgb[1]:02x}{color_rgb[2]:02x}"
                    st.markdown(f'''<div style="display: flex; align-items: center; margin-bottom: 5px;">
                                <div style="width: 20px; height: 20px; background-color: {color_hex}; border: 1px solid #ccc; margin-right: 10px;"></div>
                                <span>{label_name} (ID: {label_id})</span>
                                </div>''', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error loading segment colors: {e}")

    def get_status_message(self) -> Optional[str]:
        """Get appropriate status message based on current state."""
        if not self._settings.get('show_overlay', False):
            return MESSAGES['enable_voxels']

        if self._voxel_mode == "individual_voxels" and not self._selected_individual_voxels:
            return MESSAGES['no_individual_voxels_selected']

        return None
