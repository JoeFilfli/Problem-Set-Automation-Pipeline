/**
 * API Client for AUB LMS
 * Handles all communication with the FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

/**
 * Build full API URL from path
 */
function buildApiUrl(path: string): string {
  const normalizedBase = API_BASE_URL.endsWith('/') 
    ? API_BASE_URL.slice(0, -1) 
    : API_BASE_URL;
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}

/**
 * Generic fetch wrapper with error handling
 */
async function fetchApi<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = buildApiUrl(path);
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
      },
    });

    if (!response.ok) {
      // Try to parse error details from response
      let errorDetail = `HTTP ${response.status}`;
      try {
        const errorData = await response.json();
        errorDetail = errorData.detail || errorData.error || errorDetail;
      } catch {
        // Ignore JSON parse errors
      }
      throw new Error(errorDetail);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error [${path}]:`, error);
    throw error;
  }
}

/**
 * GET request
 */
export async function get<T>(path: string): Promise<T> {
  return fetchApi<T>(path, {
    method: 'GET',
  });
}

/**
 * POST request with JSON body
 */
export async function post<T>(path: string, data: any): Promise<T> {
  return fetchApi<T>(path, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
}

/**
 * POST request with FormData (for file uploads)
 */
export async function postFormData<T>(path: string, formData: FormData): Promise<T> {
  return fetchApi<T>(path, {
    method: 'POST',
    body: formData,
  });
}

/**
 * DELETE request
 */
export async function del<T>(path: string): Promise<T> {
  return fetchApi<T>(path, {
    method: 'DELETE',
  });
}

/**
 * Upload file with progress tracking
 */
export async function uploadWithProgress<T>(
  path: string,
  formData: FormData,
  onProgress?: (progress: number) => void
): Promise<T> {
  const url = buildApiUrl(path);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    // Track upload progress
    if (onProgress) {
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = (event.loaded / event.total) * 100;
          onProgress(progress);
        }
      });
    }

    // Handle completion
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } catch (error) {
          reject(new Error('Failed to parse response'));
        }
      } else {
        try {
          const errorData = JSON.parse(xhr.responseText);
          reject(new Error(errorData.detail || `HTTP ${xhr.status}`));
        } catch {
          reject(new Error(`HTTP ${xhr.status}`));
        }
      }
    });

    // Handle errors
    xhr.addEventListener('error', () => {
      reject(new Error('Network error'));
    });

    xhr.addEventListener('abort', () => {
      reject(new Error('Upload aborted'));
    });

    // Send request
    xhr.open('POST', url);
    xhr.send(formData);
  });
}

export default {
  get,
  post,
  postFormData,
  del,
  uploadWithProgress,
};
