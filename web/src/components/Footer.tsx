export default function Footer() {
  return (
    <footer className="border-t border-foreground/10 py-8">
      <div className="mx-auto max-w-3xl px-4 text-center text-sm text-foreground/40">
        <p>&copy; {new Date().getFullYear()} Cici Blog. All rights reserved.</p>
      </div>
    </footer>
  );
}
