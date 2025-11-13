import React from "react";
import toast from "react-hot-toast";
import '../styles/toast.css'

export const ErrorToast: React.FC<{ message: string; toastId: string }> = ({ message, toastId }) => {
  const handleDismiss = () => {
    toast.dismiss(toastId);
  };

  return (
    <div className="toast">
      <div>
        <span>{message}</span>
      </div>
      <button
        onClick={handleDismiss}
      >
        ×
      </button>
    </div>
  );
};