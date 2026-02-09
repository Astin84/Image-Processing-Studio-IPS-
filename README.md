# IPS — Image Processing Studio

IPS (Image Processing Studio) is a GUI-based Python application developed for the **Image Processing and Fundamentals of Computer Vision** course at **Bahonar University**.  
The project provides an interactive environment for exploring spatial and frequency-domain image processing concepts using OpenCV.

---

## 🎓 Academic Purpose

IPS is designed as an **educational tool** to help students understand:

- Core image processing operations
- Noise modeling and removal
- Frequency-domain filtering using Fourier Transform
- Practical usage of OpenCV (cv2) functions

A unique feature of IPS is the **real-time OpenCV code viewer**, which displays the exact CV2 code used for each operation.

---

## 🧰 Main Features

### 📂 Image File Management
- Open images (JPG, PNG, BMP)
- Save processed images
- Reset image to the original state

---

### 🖼️ Image Visualization
- Real-time image preview
- Grayscale and color image display
- Image histogram visualization
  - Intensity histogram
  - Color channel histograms
- Automatic histogram updates after each operation

---

### 🔧 Spatial Domain Image Operations
Basic pixel-level and geometric operations implemented using OpenCV:

- Image inversion
- Image rotation
- Flip operations
- Intensity transformations

These operations demonstrate **spatial domain processing fundamentals**.

---

### 🔊 Noise Addition
IPS supports controlled noise modeling for experimentation:

- Salt & Pepper Noise
- Gaussian Noise

Noise parameters can be adjusted to study their effects on image quality and frequency components.

---

### 🧹 Denoising Filters
Common noise reduction techniques taught in image processing courses:

- Mean Filter
- Median Filter
- Gaussian Filter
- Bilateral Filter

These filters allow comparison between different denoising approaches.

---

### 🎛️ Frequency Domain Processing
IPS includes full support for Fourier-based image analysis:

- Fast Fourier Transform (FFT)
- Inverse FFT
- Frequency-domain filtering

#### Available Frequency Filters:
- Low-Pass Filter
- High-Pass Filter
- Gaussian Filter
- Notch Pass Filter
- Notch Reject Filter

These filters demonstrate how modifying frequency components affects spatial image structure.

---

### 📊 Fourier Analysis Visualization
IPS provides detailed frequency-domain visual outputs:

- Magnitude Spectrum (log scale)
- Power Spectrum
- Phase Spectrum
- Radial Average of Magnitude Spectrum (1D profile)

These visualizations help users analyze frequency distribution and image texture.

---

### 🧠 Real-Time OpenCV Code Viewer
One of the key educational features of IPS:

- Displays the **exact OpenCV (cv2) code** used for:
  - Image operations
  - Noise addition
  - Denoising
  - Frequency filtering
- Updates dynamically as operations are applied
- Helps students connect theory with real implementation

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
- Centralized code generation for CV2 viewer
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
- Spatial domain filtering
- Frequency domain filtering
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
it is a **learning-oriented studio** designed to help students visualize, experiment, and understand the fundamentals of image processing and computer vision through real code and real results.
