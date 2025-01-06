// utils/error.ts
export function handleApiError(error: any) {
  if (error instanceof Response) {
    return new Error(`HTTP error! status: ${error.status}`);
  }
  return error;
}