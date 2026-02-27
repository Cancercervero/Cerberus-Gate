Read in [English](README_en.md)

<div align="center">
  <img src="docs/assets/banner.png" alt="Cerberus Gate Banner" width="400"/>
  <h1>🛡️ SISTEMA CERBERUS GATE</h1>
  <h3>Arquitectura de Defensa Cognitiva y Enrutamiento Aislado</h3>
  <p><i>The "Cerberus Gate" Framework</i></p>
</div>

---

## 👁️ Visión General

**Cerberus Gate** es un framework de Inteligencia Artificial hiper-modular de grado táctico. A diferencia de un asistente LLM convencional, Cerberus es un ecosistema que separa las capacidades cognitivas (la IA) del control de hardware (tu PC), inyectando una capa de protección física y humana inquebrantable (**Human-in-The-Loop**).

El repositorio base contiene la arquitectura de los **6 Pilares** operativos.

## 🏗️ Los 6 Pilares de la Arquitectura

### Pilar I: El Orbe Flotante (UI Minimalista)

Un Widget estilo *Spotify Mini/Discord PIP* escrito en PyQt6. Totalmente *headless*, responde a comandos de voz (usando `faster-whisper` local) e interacciones táctiles directas sin acaparar el escritorio. Parpadea en diferentes colores según su estado (escucha, advertencia, ejecución).

### Pilar II: Cerebro Nubular (Prompt Engineering Dinámico)

El "CEO" de Cerberus. Intercepta tus peticiones e inyecta el "Contexto Total del Workspace" hacia `gemini-2.5-flash`. Este proceso genera internamente **Agentes Expertos** sobre la marcha, dotando a la IA de una personalidad hiper-enfocada (Ingeniero UI, Especialista en Bases de Datos) antes de abordar la subtarea.

### Pilar III: La Pecera (Linux Sandbox Cautivo)

Todo el código generado o descargado por el Cerebro se ejecuta primero de manera aislada dentro de un entorno cautivo (WSL Ubuntu). La IA tiene la libertad de fallar, explorar y armar ahí su propio prototipo, sin tocar el Host de Windows. Solamente cuando el código supera el Test de Sintaxis, adquiere la bandera `CERTIFICADO_SEGURO`.

### Pilar IV: El Muro Blindado (Host Router Zero-Trust)

Solo el código empaquetado y seguro cruza a la red Host (Windows). Aún así, un escáner estricto revisa intenciones letales de disco o red (`os.remove`, `rmtree`, `requests`). Si detecta un vector sensible, detiene la ejecución, el Orbe parpadea en ámbar, y Cerberus solicita la aprobación del humano Commander.

### Pilar V: Sistema Inmunológico Autónomo

Si un código logra inyectar inestabilidad o resulta ser ofuscado/malicioso, Cerberus intercepta el crasheo, solicita una autopsia forense a la nube, extrae el error como un 'vector', lo almacena en su Bóveda y auto-aplica un filtro de Blacklisting para que jamás vuelva a suceder.

### Pilar VI: El Guante (Memoria Persistente DNS)

Las inteligencias artificiales nacen amnésicas en cada ejecución. Cerberus Megazord incluye un registro `user_dna.json` en su núcleo. Detecta regaños, instrucciones repetitivas o preferencias implícitas, las condensa silenciosamente y las "tatúa" en su ADN para usarlas en cada arranque de por vida.

## 🚀 Instalación y Despliegue

```bash
# 1. Clonar el núcleo Cerberus Gate
git clone https://github.com/Cancercervero/Cerberus-Gate.git

# 2. Entrar al enrutador base
cd "Cerberus-Gate"

# 3. Inicializar entorno y lanzar el Orbe
./lanzar_naranja.bat
```

> [!NOTE]
> Se requiere tener instalado **WSL2** en la máquina Windows para el módulo de cuarentena (La Pecera) y establecer las llaves API de `GEMINI_API_KEY` en el archivo `.env`.

---
<div align="center">
  <p>Construido por <b>CC IA Consultores</b></p>
  <p><i>The Future is Autonomous, The Execution is Human.</i></p>
</div>
