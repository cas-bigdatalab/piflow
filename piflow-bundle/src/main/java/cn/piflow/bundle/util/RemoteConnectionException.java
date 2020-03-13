package cn.piflow.bundle.util;

/**
 * Exception thrown when the user has requested a task cancellation.
 */

public class RemoteConnectionException extends Exception {

    /**
     *
     */
    public RemoteConnectionException() {
        super();
    }

    /**
     * @param message
     */
    public RemoteConnectionException(String message) {
        super(message);
    }

    /**
     * @param cause
     */
    public RemoteConnectionException(Throwable cause) {
        super(cause);
    }

    /**
     * @param message
     * @param cause
     */
    public RemoteConnectionException(String message, Throwable cause) {
        super(message, cause);
    }

    public static boolean isTaskCancellation(Throwable e) {
        if (e == null) {
            return false;
        } else if (e instanceof RemoteConnectionException) {
            return true;
        } else {
            return isTaskCancellation(e.getCause());
        }
    }
}
