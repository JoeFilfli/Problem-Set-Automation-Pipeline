/**
 * Helper functions for image handling in submissions
 */

/**
 * Reconstruct markdown with base64 images from image array
 * Replaces image:0, image:1, etc. with actual base64 data
 */
export function reconstructMarkdownWithImages(
    markdown: string,
    images: string[]
): string {
    if (!images || images.length === 0) {
        return markdown;
    }

    let result = markdown;
    images.forEach((base64Data, index) => {
        // Replace placeholder with actual base64 image
        const placeholderRegex = new RegExp(
            `!\\[([^\\]]*)\\]\\(image:${index}\\)`,
            'g'
        );
        result = result.replace(placeholderRegex, `![$1](${base64Data})`);
    });

    return result;
}

/**
 * Extract images from markdown text
 * Returns array of base64 image data URLs
 */
export function extractImagesFromMarkdown(markdown: string): string[] {
    const imageRegex = /!\[([^\]]*)\]\((data:image\/[^;]+;base64,[^)]+)\)/g;
    const images: string[] = [];
    let match;

    while ((match = imageRegex.exec(markdown)) !== null) {
        images.push(match[2]); // base64 data URL
    }

    return images;
}

/**
 * Strip base64 images from markdown, replacing them with placeholders
 * Returns { text, images } where text has placeholders and images is array of base64
 */
export function stripImagesFromMarkdown(markdown: string): {
    text: string;
    images: string[];
} {
    const imageRegex = /!\[([^\]]*)\]\((data:image\/[^;]+;base64,[^)]+)\)/g;
    const images: string[] = [];
    let text = markdown;
    let imageIndex = 0;
    let match;

    // Reset regex
    imageRegex.lastIndex = 0;

    while ((match = imageRegex.exec(markdown)) !== null) {
        const fullMatch = match[0];
        const altText = match[1];
        const base64Data = match[2];

        images.push(base64Data);

        // Replace with placeholder
        text = text.replace(fullMatch, `![${altText || `Image ${imageIndex + 1}`}](image:${imageIndex})`);
        imageIndex++;
    }

    return { text, images };
}
