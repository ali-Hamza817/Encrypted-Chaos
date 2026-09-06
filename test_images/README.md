# Test images

Upload these in the app (**http://localhost:5173**), keep the cipher set to the
default **Weak chaos cipher**, and press **Run the AI attack**. The model was
trained at 32x32; the app resizes every upload to that automatically.

"Structure recovered" is the SSIM shown in the app (x100). "Beat blind guess"
is that minus the ~31% a constant average-image prediction scores.

## What each file should do

| File | Matched cipher | Beat blind guess | + Pixel shuffling ON | + Wrong password |
|---|---|---|---|---|
| `in_distribution/sample_1.png` | **80%** structure | +48 pts | -1% (collapses) | -4% (collapses) |
| `in_distribution/sample_2.png` | **84%** structure | +52 pts | 13% (collapses) | -2% (collapses) |
| `in_distribution/sample_3.png` | **76%** structure | +45 pts | 4% (collapses) | -8% (collapses) |
| `in_distribution/sample_4.png` | **75%** structure | +43 pts | -1% (collapses) | -0% (collapses) |
| `in_distribution/sample_5.png` | **86%** structure | +54 pts | 11% (collapses) | -6% (collapses) |
| `in_distribution/sample_6.png` | **87%** structure | +55 pts | 3% (collapses) | -0% (collapses) |
| `out_of_distribution/text.png` | **44%** structure | +13 pts | -0% (collapses) | 6% (collapses) |
| `out_of_distribution/checkerboard.png` | **80%** structure | +49 pts | 3% (collapses) | -4% (collapses) |
| `out_of_distribution/photo_like.png` | **50%** structure | +18 pts | 4% (collapses) | 2% (collapses) |
| `out_of_distribution/pure_noise.png` | **28%** structure | -3 pts | 2% (collapses) | -0% (collapses) |

## How to know the model is working

1. **It recovers the in-distribution samples.** Upload any `in_distribution/*.png`
   with the matched **Weak chaos cipher** -> the app should say *"The attack worked"*
   and show a recovered image that clearly resembles the original (structure ~60-85%,
   beating the blind-guess baseline by a wide margin).

2. **It collapses when you change the cipher.** Same image, turn **Pixel shuffling**
   ON (or raise Passes) and re-run -> recovery drops to a few percent and the verdict
   flips to *"The attack failed"*. The model learned *this* cipher's inverse, not magic.

3. **It collapses on a wrong password.** In advanced settings, change the password by
   one character -> recovery collapses. A static-key attack only inverts the key it
   was trained on (this is the RQ1 vs RQ2 gap in the research).

4. **It degrades on out-of-distribution images.** `text.png` and `photo_like.png`
   (sharp edges / smooth gradients unlike the training style) recover only partially,
   and `pure_noise.png` not at all (SSIM on noise-vs-noise is meaningless, gain <= 0).
   `checkerboard.png` still recovers well - it is trivially low-entropy. The CNN
   learned a smooth approximation tuned to the training image style, not an exact
   decryptor. Expected and honest.

5. **AES and the hardened chaos ciphers never recover anything** (~5%, *"attack
   failed"*) for any image. That contrast is the whole point.

If 1-3 hold, the pipeline (encryption -> model -> scoring) is wired correctly.