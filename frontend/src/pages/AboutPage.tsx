import React from 'react';
import {
  BookOpen,
  Cpu,
  Eye,
  Layers,
  ShieldCheck,
  CheckCircle,
  ExternalLink
} from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <div className="space-y-6 max-w-4xl text-xs">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight m-0 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-purple-400" />
          <span>About AutoVision AI</span>
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Academic Project Documentation • B.Tech Third-Year Deep Learning Course Project
        </p>
      </div>

      {/* Problem Statement & Objective */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md space-y-2.5">
          <h3 className="text-sm font-bold text-cyan-400 uppercase tracking-wider m-0">
            1. Problem Statement
          </h3>
          <p className="text-slate-300 leading-relaxed m-0">
            Traditional traffic surveillance relies heavily on manual observation or primitive inductive loop sensors that suffer from wear-and-tear, high maintenance costs, and an inability to classify complex multi-modal traffic (cars, trucks, buses, motorcycles, bicycles). Video-based autonomous detection provides non-intrusive, scalable, and intelligent roadway telemetry.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md space-y-2.5">
          <h3 className="text-sm font-bold text-emerald-400 uppercase tracking-wider m-0">
            2. Project Objective
          </h3>
          <p className="text-slate-300 leading-relaxed m-0">
            The core objective of <strong>AutoVision AI</strong> is to design and implement an end-to-end deep learning pipeline that ingests road traffic video recordings, performs frame-by-frame object detection, classifies vehicles across 5 standard categories, assigns persistent tracking identities to avoid duplicate counting, and outputs downloadable annotated video and structured CSV reports.
          </p>
        </div>
      </div>

      {/* Methodology Section */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md space-y-4">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider m-0 flex items-center gap-2">
          <Layers className="w-4 h-4 text-blue-400" />
          <span>3. Deep Learning Methodology</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-1">
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <div className="text-cyan-400 font-bold text-sm">YOLOv8 Object Detection</div>
            <p className="text-slate-400 leading-relaxed m-0">
              Utilizes single-stage convolutional anchors to predict bounding box coordinates and class probability distributions simultaneously in a single forward pass, ensuring high inference speeds suitable for student hardware.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <div className="text-emerald-400 font-bold text-sm">OpenCV Frame Extraction</div>
            <p className="text-slate-400 leading-relaxed m-0">
              Decodes compressed video containers (MP4, AVI, MOV), extracts uncompressed RGB numpy matrices, draws bounding box overlays with class confidence labels, and encodes annotated video frames with native codecs.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <div className="text-purple-400 font-bold text-sm">ByteTrack Multi-Object Tracking</div>
            <p className="text-slate-400 leading-relaxed m-0">
              Associates vehicle centroids across adjacent video frames using Kalman filtering and Intersection-over-Union (IoU) matching. This assigns persistent Track IDs, ensuring accurate unique counts without duplicate accumulation.
            </p>
          </div>
        </div>
      </div>

      {/* Supported Classes */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md space-y-3">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider m-0 flex items-center gap-2">
          <Eye className="w-4 h-4 text-cyan-400" />
          <span>4. Supported Vehicle Classifications</span>
        </h3>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-1">
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center space-y-1">
            <div className="font-bold text-blue-400">Car</div>
            <div className="text-[10px] text-slate-500">COCO Class #2</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center space-y-1">
            <div className="font-bold text-amber-400">Truck</div>
            <div className="text-[10px] text-slate-500">COCO Class #7</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center space-y-1">
            <div className="font-bold text-emerald-400">Bus</div>
            <div className="text-[10px] text-slate-500">COCO Class #5</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center space-y-1">
            <div className="font-bold text-purple-400">Motorcycle</div>
            <div className="text-[10px] text-slate-500">COCO Class #3</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center space-y-1">
            <div className="font-bold text-yellow-400">Bicycle</div>
            <div className="text-[10px] text-slate-500">COCO Class #1</div>
          </div>
        </div>
      </div>

      {/* Academic Citation & Foundation Attribution */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md space-y-3">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider m-0 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-cyan-400" />
          <span>5. Academic Pedigree & MIT Attribution</span>
        </h3>

        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-2 text-slate-300">
          <div className="font-semibold text-slate-200">
            Foundation Repository: <em>vehicle_counting_tensorflow</em> (2018)
          </div>
          <p className="text-slate-400 leading-relaxed m-0 text-[11px]">
            Original work by <strong>Ahmet Özlü</strong> provided early prototypes for TensorFlow 1.x SSD-MobileNet video detection and traffic measurement. In this B.Tech Deep Learning course project, the codebase was modernized to PyTorch 2.15, Ultralytics YOLOv8, ByteTrack ID tracking, FastAPI backend APIs, and a modern React 19 + Tailwind CSS user interface under the terms of the MIT License.
          </p>
        </div>
      </div>
    </div>
  );
};
