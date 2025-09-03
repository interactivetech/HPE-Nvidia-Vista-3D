import streamlit as st
import pyvista as pv
from stpyvista import stpyvista

st.set_page_config(layout="wide", page_title="Minimal PyVista Test")

st.header("Minimal PyVista Test")

# Create a simple PyVista object (e.g., a sphere)
mesh = pv.Sphere()

# Create a PyVista plotter
plotter = pv.Plotter(window_size=[800, 600], border=False)
plotter.background_color = 'black'
plotter.add_mesh(mesh, color='red')
plotter.camera_position = 'iso'
plotter.camera.zoom(1.5)

# Display the plotter
stpyvista(plotter, key="minimal_pv_viewer")

#st.write("If you see a red sphere above, stpyvista is working!")
