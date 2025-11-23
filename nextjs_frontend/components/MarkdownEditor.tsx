'use client';

import { useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

interface MarkdownEditorProps {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    disabled?: boolean;
    minHeight?: string;
}

/**
 * Rich Markdown Editor with LaTeX and Image Support
 * Allows students to write formatted solutions with math and images
 */
export default function MarkdownEditor({
    value,
    onChange,
    placeholder = 'Write your solution here...',
    disabled = false,
    minHeight = '300px'
}: MarkdownEditorProps) {
    const [showPreview, setShowPreview] = useState(false);
    const [uploadingImage, setUploadingImage] = useState(false);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Insert text at cursor position
    const insertText = (before: string, after: string = '', placeholderText: string = '') => {
        if (!textareaRef.current) return;

        const textarea = textareaRef.current;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const selectedText = value.substring(start, end) || placeholderText;

        const newText =
            value.substring(0, start) +
            before + selectedText + after +
            value.substring(end);

        onChange(newText);

        // Set cursor position after insertion
        setTimeout(() => {
            textarea.focus();
            const newCursorPos = start + before.length + selectedText.length;
            textarea.setSelectionRange(newCursorPos, newCursorPos);
        }, 0);
    };

    // Handle image upload
    const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        // Validate file type
        if (!file.type.startsWith('image/')) {
            alert('Please upload an image file');
            return;
        }

        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            alert('Image size should be less than 5MB');
            return;
        }

        setUploadingImage(true);

        try {
            // Convert image to base64
            const reader = new FileReader();
            reader.onload = async () => {
                const base64 = reader.result as string;

                try {
                    // Upload to backend
                    const response = await fetch('/api/py/images/upload', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            image_data: base64,
                            filename: file.name
                        })
                    });

                    if (!response.ok) {
                        throw new Error('Failed to upload image');
                    }

                    const data = await response.json();
                    const imageId = data.image_id;

                    // Insert reference to image (not base64!)
                    const imageMarkdown = `\n![${file.name}](/api/py/images/${imageId})\n`;

                    // Insert at cursor position
                    if (textareaRef.current) {
                        const start = textareaRef.current.selectionStart;
                        const newText =
                            value.substring(0, start) +
                            imageMarkdown +
                            value.substring(start);
                        onChange(newText);
                    }
                } catch (error) {
                    console.error('Error uploading image:', error);
                    alert('Failed to upload image to server');
                }
            };
            reader.readAsDataURL(file);
        } catch (error) {
            console.error('Error processing image:', error);
            alert('Failed to process image');
        } finally {
            setUploadingImage(false);
            // Reset file input
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    return (
        <div className="border border-gray-300 rounded-aub overflow-hidden bg-white">
            {/* Toolbar */}
            <div className="bg-gray-50 border-b border-gray-300 px-3 py-2 flex items-center gap-2 flex-wrap">
                {/* View Toggle */}
                <div className="flex items-center gap-1 mr-2">
                    <button
                        type="button"
                        onClick={() => setShowPreview(false)}
                        disabled={disabled}
                        className={`px-3 py-1 text-sm font-medium rounded transition-colors ${!showPreview
                                ? 'bg-white text-aub-red border border-gray-300'
                                : 'text-gray-700 hover:text-gray-900'
                            }`}
                    >
                        ✏️ Edit
                    </button>
                    <button
                        type="button"
                        onClick={() => setShowPreview(true)}
                        disabled={disabled}
                        className={`px-3 py-1 text-sm font-medium rounded transition-colors ${showPreview
                                ? 'bg-white text-aub-red border border-gray-300'
                                : 'text-gray-700 hover:text-gray-900'
                            }`}
                    >
                        👁️ Preview
                    </button>
                </div>

                <div className="h-6 w-px bg-gray-300"></div>

                {/* Formatting Buttons */}
                <button
                    type="button"
                    onClick={() => insertText('**', '**', 'bold text')}
                    disabled={disabled || showPreview}
                    className="toolbar-btn"
                    title="Bold (Ctrl+B)"
                >
                    <strong>B</strong>
                </button>

                <button
                    type="button"
                    onClick={() => insertText('*', '*', 'italic text')}
                    disabled={disabled || showPreview}
                    className="toolbar-btn"
                    title="Italic (Ctrl+I)"
                >
                    <em>I</em>
                </button>

                <button
                    type="button"
                    onClick={() => insertText('# ', '', 'Heading')}
                    disabled={disabled || showPreview}
                    className="toolbar-btn"
                    title="Heading"
                >
                    H
                </button>

                <div className="h-6 w-px bg-gray-300"></div>

                {/* Math Buttons */}
                <button
                    type="button"
                    onClick={() => insertText('$', '$', 'x^2')}
                    disabled={disabled || showPreview}
                    className="toolbar-btn"
                    title="Inline Math"
                >
                    𝑥²
                </button>

                <button
                    type="button"
                    onClick={() => insertText('\n$$\n', '\n$$\n', 'E = mc^2')}
                    disabled={disabled || showPreview}
                    className="toolbar-btn"
                    title="Block Math"
                >
                    ∑
                </button>

                <div className="h-6 w-px bg-gray-300"></div>

                {/* List Buttons */}
                <button
                    type="button"
                    onClick={() => insertText('\n- ', '', 'List item')}
                    disabled={disabled || showPreview}
                    className="toolbar-btn"
                    title="Bullet List"
                >
                    • List
                </button>

                <button
                    type="button"
                    onClick={() => insertText('\n1. ', '', 'List item')}
                    disabled={disabled || showPreview}
                    className="toolbar-btn"
                    title="Numbered List"
                >
                    1. List
                </button>

                <div className="h-6 w-px bg-gray-300"></div>

                {/* Image Upload */}
                <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={disabled || showPreview || uploadingImage}
                    className="toolbar-btn"
                    title="Upload Image"
                >
                    {uploadingImage ? '⏳' : '🖼️'} Image
                </button>
                <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    className="hidden"
                />

                {/* Help */}
                <div className="ml-auto text-xs text-gray-600">
                    <a
                        href="https://www.markdownguide.org/basic-syntax/"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-aub-red hover:underline"
                    >
                        Markdown Guide
                    </a>
                    {' • '}
                    <a
                        href="https://katex.org/docs/supported.html"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-aub-red hover:underline"
                    >
                        LaTeX Reference
                    </a>
                </div>
            </div>

            {/* Content Area */}
            <div className="relative" style={{ minHeight }}>
                {!showPreview ? (
                    /* Editor */
                    <textarea
                        ref={textareaRef}
                        value={value}
                        onChange={(e) => onChange(e.target.value)}
                        placeholder={placeholder}
                        disabled={disabled}
                        className="w-full p-4 font-mono text-sm text-gray-900 resize-none focus:outline-none"
                        style={{ minHeight }}
                    />
                ) : (
                    /* Preview */
                    <div className="p-4 overflow-auto" style={{ minHeight }}>
                        {value ? (
                            <div className="prose prose-sm max-w-none [&_.katex]:text-base [&_.katex-display]:my-4 [&_img]:max-w-full [&_img]:h-auto [&_img]:rounded [&_img]:shadow-md">
                                <ReactMarkdown
                                    remarkPlugins={[remarkGfm, remarkMath]}
                                    rehypePlugins={[rehypeKatex]}
                                >
                                    {value.replace(/\\\[/g, '$$').replace(/\\\]/g, '$$').replace(/\\\(/g, '$').replace(/\\\)/g, '$')}
                                </ReactMarkdown>
                            </div>
                        ) : (
                            <p className="text-gray-400 italic">Nothing to preview yet...</p>
                        )}
                    </div>
                )}
            </div>

            {/* Footer Tips */}
            <div className="bg-gray-50 border-t border-gray-300 px-4 py-2 text-xs text-gray-600">
                <div className="flex flex-wrap gap-4">
                    <span><strong>Bold:</strong> **text**</span>
                    <span><strong>Italic:</strong> *text*</span>
                    <span><strong>Inline Math:</strong> $x^2$</span>
                    <span><strong>Block Math:</strong> $$E=mc^2$$</span>
                    <span><strong>Image:</strong> Use upload button or ![alt](url)</span>
                </div>
            </div>
        </div>
    );
}
