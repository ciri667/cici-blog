"use client";

import { useRef, useState, DragEvent, ClipboardEvent } from "react";
import MarkdownRenderer from "./MarkdownRenderer";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
}

async function uploadImage(file: File): Promise<string> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    credentials: "include",
    body: form,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "上传失败");
  }
  const data = await res.json();
  return data.url;
}

export default function MarkdownEditor({ value, onChange }: MarkdownEditorProps) {
  const [preview, setPreview] = useState(false);
  const [uploading, setUploading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function insertAtCursor(text: string) {
    const ta = textareaRef.current;
    if (!ta) {
      onChange(value + text);
      return;
    }
    const start = ta.selectionStart;
    const end = ta.selectionEnd;
    const newValue = value.slice(0, start) + text + value.slice(end);
    onChange(newValue);
    // Restore cursor position after React re-render
    requestAnimationFrame(() => {
      ta.selectionStart = ta.selectionEnd = start + text.length;
      ta.focus();
    });
  }

  async function handleFiles(files: FileList | File[]) {
    const imageFiles = Array.from(files).filter((f) =>
      f.type.startsWith("image/"),
    );
    if (imageFiles.length === 0) return;

    setUploading(true);
    try {
      for (const file of imageFiles) {
        const url = await uploadImage(file);
        insertAtCursor(`![${file.name}](${url})\n`);
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : "图片上传失败");
    } finally {
      setUploading(false);
    }
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    if (e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  }

  function handlePaste(e: ClipboardEvent) {
    const items = e.clipboardData.items;
    const images: File[] = [];
    for (const item of items) {
      if (item.type.startsWith("image/")) {
        const file = item.getAsFile();
        if (file) images.push(file);
      }
    }
    if (images.length > 0) {
      e.preventDefault();
      handleFiles(images);
    }
  }

  return (
    <div className="rounded-md border border-foreground/20">
      <div className="flex items-center border-b border-foreground/10">
        <button
          type="button"
          onClick={() => setPreview(false)}
          className={`px-4 py-2 text-sm ${!preview ? "border-b-2 border-foreground font-medium" : "text-foreground/50"}`}
        >
          编辑
        </button>
        <button
          type="button"
          onClick={() => setPreview(true)}
          className={`px-4 py-2 text-sm ${preview ? "border-b-2 border-foreground font-medium" : "text-foreground/50"}`}
        >
          预览
        </button>
        {uploading && (
          <span className="ml-auto pr-4 text-xs text-foreground/50">
            上传中...
          </span>
        )}
      </div>

      {preview ? (
        <div className="min-h-[400px] p-4">
          {value ? (
            <MarkdownRenderer content={value} />
          ) : (
            <p className="text-foreground/40">暂无内容</p>
          )}
        </div>
      ) : (
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onPaste={handlePaste}
          className="block min-h-[400px] w-full resize-y bg-transparent p-4 font-mono text-sm focus:outline-none"
          placeholder="使用 Markdown 编写文章内容...（支持拖拽或粘贴上传图片）"
        />
      )}
    </div>
  );
}
