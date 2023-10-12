use std::ffi::CString;
use std::os::raw::c_char;

fn get_message(hello: bool) -> String {
    if hello {
        "Hello, world!".to_string()
    } else {
        "Bye bye".to_string()
    }
}

#[no_mangle]
pub extern "C" fn rust_sample_get_message(hello: bool) -> *mut c_char {
    CString::into_raw(CString::new(get_message(hello)).unwrap())
}

#[cfg(target_os = "android")]
mod android_bindings {
    use jni::JNIEnv;
    use jni::objects::JObject;
    use jni::sys::{jstring, jboolean, JNI_FALSE};
    #[no_mangle]
    pub unsafe extern "C" fn Java_com_nordsec_rust_1sample_RustSample_get_1message(
        env: JNIEnv,
        _: JObject,
        hello: jboolean,
    ) -> jstring {
        env.new_string(super::get_message(hello != JNI_FALSE)).unwrap().into_inner()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_message() {
        assert_eq!(get_message(true), "Hello, world!");
    }

    #[test]
    fn test_rust_sample_get_message() {
        let msg = rust_sample_get_message(false);

        unsafe { assert_eq!(CString::from_raw(msg).into_string().unwrap(), "Bye bye") }
    }
}
