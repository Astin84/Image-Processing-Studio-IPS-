# IPS — Image Processing Studio

IPS (Image Processing Studio) is a GUI-based Python application developed for the  
**Image Processing and Fundamentals of Computer Vision** course at **Bahonar University**.

It provides an interactive environment for exploring **spatial and frequency-domain**
image processing concepts using OpenCV, with real-time visualization and code display.

---

## 🖥️ Main Environment

The main workspace of IPS includes image preview, histograms, tool panels,
and a real-time OpenCV code viewer.

![Main Environment](IPS_Pics/mainEnv.png)

---

## 🎓 Academic Purpose

IPS is designed as an **educational tool** to help students understand:

- Digital image processing fundamentals
- Noise modeling and removal
- Frequency-domain analysis using Fourier Transform
- Practical usage of OpenCV (cv2) functions

A key educational feature is the **real-time CV2 code displayer**.

---

## 🧰 Tools Overview

All processing tools are grouped into logical sections for ease of use.

![Tools Panel](IPS_Pics/Tools.png)

---

## 🖼️ Image Visualization

IPS provides real-time visualization tools:

- Image preview
- Grayscale and color display
- Histogram visualization

### Color Histogram

Displays intensity distribution for grayscale and RGB channels.

![Color Histogram](IPS_Pics/ColorHist.png)

### Visual Tools

Controls related to visualization and display settings.

![Visual Tools](IPS_Pictures/Visual Tools.png)

---

## 🔧 Spatial Domain Image Operations

Basic image manipulation tools implemented using OpenCV:

- Image inversion
- Rotation
- Flip operations
- Intensity transformations

![Image Operations Tools](IPS_Pictures/Operations Tools.png)

These operations demonstrate **spatial-domain processing fundamentals**.

---

## 🔊 Noise Addition

IPS supports controlled noise modeling for experimentation:

- Salt & Pepper Noise
- Gaussian Noise

Noise parameters can be adjusted to study their effect on image quality.

![Add Noise Tools](IPS_Pictures/AddNoise Tools.png)

---

## 🧹 Denoising Filters

Common noise removal techniques taught in image processing courses:

- Mean Filter
- Median Filter
- Gaussian Filter
- Bilateral Filter

![Denoise Tools](IPS_Pics/DenoiseTool.png)

These filters allow comparison between different denoising approaches.

---

## 🎛️ Frequency Domain Processing

IPS includes full support for Fourier-based image analysis.

### Frequency Filters:
- Low-Pass Filter
- High-Pass Filter
- Gaussian Filter
- Notch Pass Filter
- Notch Reject Filter

![Frequency Tools](IPS_Pictures/Frequencies Tools.png)

---

## 📊 Fourier Analysis

The Fourier Analysis section provides detailed frequency-domain visualization:

- Magnitude Spectrum (log scale)
- Power Spectrum
- Phase Spectrum
- Radial Average of Magnitude Spectrum (1D profile)

![Fourier Analysis](IPS_Pictures/Fourier Analysis.png)

These visualizations help analyze frequency distribution and texture information.

---

## 🧠 Real-Time OpenCV Code Viewer

One of the most important educational features of IPS:

- Displays the **exact OpenCV (cv2) code** used for:
  - Image operations
  - Noise addition
  - Denoising filters
  - Frequency-domain filters
- Updates dynamically as operations are applied

![CV2 Code Viewer](IPS_Pics/Cv2CodeDisplayer.png)

This helps students connect **theory with implementation**.

---

## 🧱 Software Architecture

- Language: Python
- Libraries:
  - OpenCV (cv2)
  - NumPy
  - Matplotlib
- GUI-based desktop application

### Design Principles:
- Separation of original and processed images
- Modular processing functions
- Centralized CV2 code generation
- Real-time visualization updates

---

## 🔄 Typical Workflow

1. Load an image
2. Inspect histogram and visualization
3. Add noise
4. Apply denoising filters
5. Perform Fourier analysis
6. Apply frequency-domain filters
7. View OpenCV code in real time
8. Save the final image

---

## 📚 Topics Covered

- Digital image processing
- Spatial-domain filtering
- Frequency-domain filtering
- Noise modeling
- Fourier Transform
- Histogram analysis
- Practical OpenCV programming

---

## 🧪 Intended Audience

- Undergraduate students
- Computer vision beginners
- Image processing laboratory courses
- Anyone learning OpenCV fundamentals

---

## 📄 License

This project is released under the **MIT License**  
Free to use for educational and academic purposes.

---

## 🤝 Contributions

Contributions and improvements are welcome.

- Open an issue for bugs or suggestions
- Submit pull requests for enhancements

---

## 📌 Final Note

IPS is not just an image processing tool —  
it is a **learning-oriented studio** designed to help students visualize,
experiment, and understand image processing and computer vision through
real code and real results.
