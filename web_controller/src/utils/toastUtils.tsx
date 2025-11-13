import toast from "react-hot-toast";
import { ErrorToast } from "../components/ErrorToast";

export const showErrorToast = (message: string) => {
  toast.custom((t) => (
    <ErrorToast 
      message={message}
      toastId={t.id}
    />
  ), {
    duration: Infinity,
  });

};