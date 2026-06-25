"use client";

import { useSession } from "next-auth/react";

import { AppShell } from "@/components/layout/app-shell";
import { ThemeToggle } from "@/components/shared/theme-toggle";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function SettingsPage() {
  const { data: session } = useSession();

  return (
    <AppShell title="Settings" description="Manage your account and preferences">
      <Tabs defaultValue="account" className="max-w-2xl">
        <TabsList>
          <TabsTrigger value="account">Account</TabsTrigger>
          <TabsTrigger value="appearance">Appearance</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
        </TabsList>

        <TabsContent value="account" className="mt-6 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Account</CardTitle>
              <CardDescription>Your account information</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-muted-foreground">Name</Label>
                <p className="font-medium">{session?.user?.name}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Email</Label>
                <p className="font-medium">{session?.user?.email}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Role</Label>
                <p className="font-medium capitalize">{session?.user?.role}</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="appearance" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Appearance</CardTitle>
              <CardDescription>Customize how GradPilot looks</CardDescription>
            </CardHeader>
            <CardContent className="flex items-center justify-between">
              <div>
                <Label>Theme</Label>
                <p className="text-sm text-muted-foreground">Toggle between light and dark mode</p>
              </div>
              <ThemeToggle />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
              <CardDescription>Choose what you want to be notified about</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                { id: "deadlines", label: "Deadline reminders", desc: "Get notified before application deadlines" },
                { id: "documents", label: "Document processing", desc: "When documents are parsed and validated" },
                { id: "ai", label: "AI insights", desc: "New recommendations and profile analysis" },
              ].map((pref) => (
                <div key={pref.id}>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor={pref.id}>{pref.label}</Label>
                      <p className="text-sm text-muted-foreground">{pref.desc}</p>
                    </div>
                    <Switch id={pref.id} defaultChecked aria-label={pref.label} />
                  </div>
                  <Separator className="mt-4" />
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </AppShell>
  );
}
