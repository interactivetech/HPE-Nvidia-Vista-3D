"""
Template Renderer for Vista3D Application
Handles rendering of HTML templates with dynamic data injection.
"""

import json
from typing import Dict, Any
from pathlib import Path
from jinja2 import Template, Environment, FileSystemLoader


class TemplateRenderer:
    """
    Renders HTML templates with dynamic data using Jinja2.
    """

    def __init__(self, template_dir: str = "assets"):
        self.template_dir = Path(template_dir)
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def render_template(
        self,
        template_name: str,
        **kwargs
    ) -> str:
        """
        Render a template with provided data.
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**kwargs)
        except Exception as e:
            print(f"Error rendering template {template_name}: {e}")
            return self._render_fallback_html()

    def render_viewer(
        self,
        volume_list_js: str,
        overlay_colors_js: str,
        custom_colormap_js: str,
        **kwargs
    ) -> str:
        """
        Render the NiiVue viewer template with provided data.
        """
        try:
            # Load the Niivue JavaScript library content
            niivue_lib_path = Path(__file__).parent.parent / 'assets' / 'niivue.umd.js'
            with open(niivue_lib_path, 'r') as f:
                niivue_lib_content = f.read()

            template = self.env.get_template('niivue_viewer.html')

            # Prepare template variables
            template_vars = {
                'niivue_lib_content': niivue_lib_content,
                'volume_list_js': volume_list_js,
                'overlay_colors_js': overlay_colors_js,
                'custom_colormap_js': custom_colormap_js,
                'image_server_url': kwargs.get('image_server_url', ''),
                'main_is_nifti': kwargs.get('main_is_nifti', True),
                'main_vol': kwargs.get('main_vol', True),
                'color_map_js': kwargs.get('color_map_js', '"gray"'),
                'nifti_gamma': kwargs.get('nifti_gamma', 1.0),
                'nifti_opacity': kwargs.get('nifti_opacity', 1.0),
                'window_center': kwargs.get('window_center', 0),
                'window_width': kwargs.get('window_width', 1000),
                'overlay_start_index': kwargs.get('overlay_start_index', 0),
                'actual_slice_type': kwargs.get('actual_slice_type', 3),
                'segment_opacity': kwargs.get('segment_opacity', 0.5),
            }

            return template.render(**template_vars)

        except Exception as e:
            print(f"Error rendering viewer template: {e}")
            return self._render_fallback_html()

    def _render_fallback_html(self) -> str:
        """Render a basic fallback HTML if template rendering fails."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { margin: 20px; font-family: Arial, sans-serif; }
                .error { color: red; padding: 20px; border: 1px solid red; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="error">
                <h3>Viewer Error</h3>
                <p>Unable to load the NiiVue viewer. Please check the application configuration.</p>
            </div>
        </body>
        </html>
        """
