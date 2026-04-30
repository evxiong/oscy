import {
  Switch as AriaSwitch,
  composeRenderProps,
  type SwitchProps as AriaSwitchProps,
} from "react-aria-components";
import merge from "../_utils/merge";

export default function Switch({ children, ...props }: AriaSwitchProps) {
  return (
    <AriaSwitch
      className="group/switch flex shrink-0 flex-row items-center gap-2"
      {...props}
    >
      {composeRenderProps(children, (children) => (
        <>
          <div
            className={merge(
              "peer inline-flex h-5 w-9 shrink-0 cursor-pointer items-center gap-2 rounded-full px-0.5 transition-colors",
              "group-data-[focus-visible]/switch:ring-2 group-data-[focus-visible]/switch:ring-ring group-data-[focus-visible]/switch:ring-offset-2",
              "bg-border group-data-[selected]/switch:bg-gold",
            )}
          >
            <div
              className={merge(
                "pointer-events-none block size-4 rounded-full bg-background shadow-lg transition-transform",
                "translate-x-0 group-data-[selected]/switch:translate-x-4",
              )}
            />
          </div>
          {children}
        </>
      ))}
    </AriaSwitch>
  );
}
