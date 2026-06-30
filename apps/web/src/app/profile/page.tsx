"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, User } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { AppShell } from "@/components/layout/app-shell";
import { ListSkeleton } from "@/components/shared/loading-skeletons";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { useProfile, useProfileAnalysis, useUpdateProfile } from "@/hooks/use-queries";

const schema = z.object({
  nationality: z.string().optional(),
  target_degree: z.string().optional(),
  field_of_study: z.string().optional(),
  gpa: z.string().optional(),
  ielts_score: z.string().optional(),
  bio: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

export default function ProfilePage() {
  const { data: profile, isLoading } = useProfile();
  const { data: analysis } = useProfileAnalysis();
  const updateProfile = useUpdateProfile();

  const { register, handleSubmit, reset } = useForm<FormData>({ resolver: zodResolver(schema) });

  useEffect(() => {
    if (profile) {
      reset({
        nationality: profile.nationality ?? "",
        target_degree: profile.target_degree ?? "",
        field_of_study: profile.field_of_study ?? "",
        gpa: profile.gpa != null ? String(profile.gpa) : "",
        ielts_score: profile.test_scores?.ielts != null ? String(profile.test_scores.ielts) : "",
        bio: profile.bio ?? "",
      });
    }
  }, [profile, reset]);

  function onSubmit(data: FormData) {
    updateProfile.mutate({
      nationality: data.nationality || null,
      target_degree: data.target_degree || null,
      field_of_study: data.field_of_study || null,
      gpa: data.gpa ? Number(data.gpa) : null,
      test_scores: data.ielts_score ? { ielts: Number(data.ielts_score) } : null,
      bio: data.bio || null,
    });
  }

  return (
    <AppShell title="Profile" description="Build your student profile for smarter recommendations">
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          {isLoading ? (
            <ListSkeleton count={1} />
          ) : (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" aria-hidden />
                  Student Profile
                </CardTitle>
                <CardDescription>This information powers your Digital Twin and AI recommendations.</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit(onSubmit)} className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="nationality">Nationality</Label>
                    <Input id="nationality" {...register("nationality")} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="target_degree">Target Degree</Label>
                    <Input id="target_degree" placeholder="MSc, PhD..." {...register("target_degree")} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="field_of_study">Field of Study</Label>
                    <Input id="field_of_study" {...register("field_of_study")} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="gpa">GPA (4.0 scale)</Label>
                    <Input id="gpa" type="number" step="0.01" {...register("gpa")} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="ielts_score">IELTS Score</Label>
                    <Input id="ielts_score" type="number" step="0.5" {...register("ielts_score")} />
                  </div>
                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="bio">Bio</Label>
                    <Textarea id="bio" rows={4} {...register("bio")} />
                  </div>
                  <div className="md:col-span-2">
                    <Button type="submit" disabled={updateProfile.isPending}>
                      {updateProfile.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                      Save profile
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          <Card className="glass">
            <CardHeader>
              <CardTitle className="text-sm">Readiness Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {analysis ? (
                <>
                  {[
                    { label: "Admission", value: analysis.admission_readiness_score },
                    { label: "Scholarship", value: analysis.scholarship_readiness_score },
                    { label: "Employability", value: analysis.employability_score },
                  ].map((item) => (
                    <div key={item.label}>
                      <div className="mb-1 flex justify-between text-sm">
                        <span>{item.label}</span>
                        <span className="text-muted-foreground">{Math.round(item.value)}%</span>
                      </div>
                      <Progress value={item.value} />
                    </div>
                  ))}
                  {analysis.strengths?.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-2">
                      {analysis.strengths.map((s) => (
                        <Badge key={s} variant="success">{s}</Badge>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <p className="text-sm text-muted-foreground">Save your profile to generate analysis.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
