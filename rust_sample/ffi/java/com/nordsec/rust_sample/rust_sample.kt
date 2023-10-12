package com.nordsec.rust_sample;

class RustSample {
  init {
    System.loadLibrary("hello")
  }
  external fun sayHello()
}
