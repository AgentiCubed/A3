/**
 * The AgentiCubed wordmark, rendered as "Agentic³" with a true math-notation
 * raised 3. The superscript is accented so it reads as the cube.
 */
export function Wordmark({ size = 28 }: { size?: number }) {
  return (
    <span
      aria-label="Agentic cubed"
      style={{
        fontWeight: 800,
        fontSize: size,
        letterSpacing: -0.5,
        color: "#e6edf3",
        whiteSpace: "nowrap",
      }}
    >
      Agentic
      <sup
        style={{
          fontSize: "0.62em",
          fontWeight: 800,
          verticalAlign: "super",
          color: "#2f6fed",
          marginLeft: 1,
        }}
      >
        3
      </sup>
    </span>
  );
}
