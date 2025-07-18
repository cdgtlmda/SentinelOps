"use server";

import { tasks } from "@trigger.dev/sdk/v3";
// Jobs example removed - not needed for SentinelOps

export async function myTask() {
  try {
    const handle = await tasks.trigger<typeof helloWorldTask>(
      "hello-world",
      "James",
    );

    return { handle };
  } catch (error) {
    console.error(error);
    return {
      error: "something went wrong",
    };
  }
}
