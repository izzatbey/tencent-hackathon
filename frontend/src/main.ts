import { mount } from 'svelte'
import '@fontsource-variable/source-serif-4'
import '@fontsource/ibm-plex-mono/400.css'
import '@fontsource/ibm-plex-mono/500.css'
import '@fontsource/ibm-plex-mono/600.css'
import './app.css'
import App from './App.svelte'

export default mount(App, { target: document.getElementById('app')! })
