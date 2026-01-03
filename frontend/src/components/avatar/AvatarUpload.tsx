"use client";

import { useState, useRef } from 'react';
import { Upload, X, Loader2 } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface AvatarUploadProps {
  currentAvatarUrl?: string | null;
  onUploadSuccess?: (newAvatarUrl: string) => void;
  className?: string;
}

export default function AvatarUpload({
  currentAvatarUrl,
  onUploadSuccess,
  className = ''
}: AvatarUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(currentAvatarUrl || null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // 验证文件类型
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      setError('Only JPG, PNG, GIF, and WebP images are allowed');
      return;
    }

    // 验证文件大小 (5MB)
    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
      setError('File size must be less than 5MB');
      return;
    }

    // 显示预览
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreviewUrl(e.target?.result as string);
    };
    reader.readAsDataURL(file);

    // 上传文件
    await uploadFile(file);
  };

  const uploadFile = async (file: File) => {
    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post<{ avatar_url: string; message: string }>(
        '/users/me/avatar',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setPreviewUrl(response.data.avatar_url);
      onUploadSuccess?.(response.data.avatar_url);
    } catch (err: any) {
      console.error('Avatar upload failed:', err);
      setError(err.response?.data?.detail || 'Failed to upload avatar');
      setPreviewUrl(currentAvatarUrl || null); // 恢复原头像
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteAvatar = async () => {
    if (!previewUrl) return;

    setUploading(true);
    setError(null);

    try {
      await apiClient.delete('/users/me/avatar');
      setPreviewUrl(null);
      onUploadSuccess?.('');
    } catch (err: any) {
      console.error('Avatar delete failed:', err);
      setError(err.response?.data?.detail || 'Failed to delete avatar');
    } finally {
      setUploading(false);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className={`flex flex-col items-center gap-4 ${className}`}>
      {/* 头像预览 */}
      <div className="relative">
        <div className="w-32 h-32 rounded-full overflow-hidden bg-gray-200 border-4 border-white shadow-lg">
          {previewUrl ? (
            <img
              src={previewUrl}
              alt="Avatar"
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-400">
              <Upload size={40} />
            </div>
          )}
        </div>

        {/* 删除按钮 */}
        {previewUrl && !uploading && (
          <button
            onClick={handleDeleteAvatar}
            className="absolute top-0 right-0 bg-red-500 text-white rounded-full p-1.5 hover:bg-red-600 transition-colors shadow-lg"
            title="Delete avatar"
          >
            <X size={16} />
          </button>
        )}

        {/* 上传中指示器 */}
        {uploading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full">
            <Loader2 className="animate-spin text-white" size={32} />
          </div>
        )}
      </div>

      {/* 上传按钮 */}
      <div className="flex flex-col items-center gap-2">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/gif,image/webp"
          onChange={handleFileSelect}
          className="hidden"
        />
        <button
          onClick={handleUploadClick}
          disabled={uploading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {uploading ? 'Uploading...' : previewUrl ? 'Change Avatar' : 'Upload Avatar'}
        </button>
        <p className="text-xs text-gray-500 text-center">
          JPG, PNG, GIF or WebP • Max 5MB
        </p>
      </div>

      {/* 错误消息 */}
      {error && (
        <div className="px-4 py-2 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}
    </div>
  );
}
