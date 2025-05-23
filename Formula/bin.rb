class Bin < Formula
  desc "ade's `~/bin`. install using `brew install adelynnmckay/tap/bin`. have fun."
  homepage ""
  url ""
  sha256 ""
  license "MIT"

  depends_on "adelynnmckay/tap/bootstrap.sh"
  depends_on "adelynnmckay/tap/lib"

  def install
    system "make", "install"
  end

  test do
    system "make", "test"
  end
end
